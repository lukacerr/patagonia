"""Grafo LangGraph que coordina planificacion, ejecucion y resumen."""

import json
from collections.abc import AsyncIterator, Sequence
from typing import Annotated, Literal, TypedDict, cast

from langchain_core.messages import (
    AIMessageChunk,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
    message_to_dict,
)
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph, add_messages

from app.agents.executor import TodoStatus, run_executor_agent
from app.agents.planner import PlannedTodo, run_planner_agent
from app.agents.summary import run_summary_agent

GraphStatus = Literal[
    "running", "success", "partial", "failed", "needs_input", "invalid_request"
]


class FinalReport(TypedDict):
    """Contrato JSON estable devuelto por API, CLI y tests."""

    status: GraphStatus
    input: str
    interpretation: str
    issues: list[str]
    todos: list[dict[str, object]]
    actions: list[dict[str, object]]
    recommendation: str | None
    trace: list[dict[str, object]]


class GraphState(TypedDict):
    """Estado interno compartido por los nodos del grafo agentico."""

    status: GraphStatus
    messages: Annotated[list[BaseMessage], add_messages]
    todos: list[PlannedTodo]
    issues: list[str]


def create_initial_state(history: Sequence[BaseMessage] | None) -> GraphState:
    """Construye el estado inicial a partir del historial recibido."""

    return {
        "status": "running",
        "messages": [*(history or [])],
        "todos": [],
        "issues": [],
    }


async def run_graph_json(history: Sequence[BaseMessage] | None) -> FinalReport:
    """Ejecuta el grafo completo y normaliza fallos inesperados como reporte."""

    prompt = _last_human_text(history or [])
    try:
        result = await graph.ainvoke(create_initial_state(history))
        return cast(FinalReport, result)
    except Exception as exc:
        return _failure_report(prompt, exc)


async def stream_graph_events(
    history: Sequence[BaseMessage] | None,
) -> AsyncIterator[str]:
    """Ejecuta el grafo y expone solo eventos SSE aptos para clientes publicos."""

    try:
        async for chunk in graph.astream(
            create_initial_state(history),
            stream_mode=["messages", "custom"],
            subgraphs=True,
            version="v2",
        ):
            async for event in _public_events(
                cast(dict[str, object], cast(object, chunk))
            ):
                yield event
    except Exception as exc:
        yield _sse(
            "error",
            {"code": type(exc).__name__, "message": str(exc)},
        )


async def planner_node(state: GraphState, config: RunnableConfig) -> dict[str, object]:
    """Interpreta el pedido y decide si existe un plan ejecutable."""

    writer = get_stream_writer()
    writer({"stage": "planning", "message": "Planificando solicitud"})

    if not _last_human_text(state["messages"]):
        return {
            "status": "invalid_request",
            "messages": [],
            "todos": [],
            "issues": ["El historial debe incluir al menos un mensaje humano"],
        }

    result_dict = await run_planner_agent(
        cast(list[AnyMessage], state["messages"]), config
    )
    result = result_dict.get("structured_response")
    messages = cast(list[BaseMessage], result_dict.get("messages", []))[
        len(state["messages"]) :
    ]

    if result is None:
        return {
            "status": "failed",
            "messages": messages,
            "issues": [
                *state["issues"],
                "El planner no devolvio una respuesta estructurada",
            ],
        }

    status: GraphStatus = result.status if result.status != "ready" else "running"
    issues = [*state["issues"], *result.missing_fields, *result.errors]
    writer({"todos": [todo.model_dump(mode="json") for todo in result.todos]})
    return {
        "status": status,
        "messages": messages,
        "todos": result.todos,
        "issues": issues,
    }


def route_after_planner(state: GraphState) -> Literal["executor", "summary"]:
    """Enruta al executor solo cuando el planner genero TODOs ejecutables."""

    if state["status"] == "running" and state["todos"]:
        return "executor"
    return "summary"


async def executor_node(state: GraphState, config: RunnableConfig) -> dict[str, object]:
    """Ejecuta TODOs con tools mockeadas y registra progreso incremental."""

    writer = get_stream_writer()
    writer({"stage": "executing", "message": "Ejecutando TODOs"})
    todos = [*state["todos"]]

    async def on_todo_update(todo_id: str, status: TodoStatus) -> None:
        todo = next((t for t in todos if t.id == todo_id), None)
        if todo and status == "completed":
            todo.done = True

        writer(
            {
                "todo_id": todo_id,
                "status": status,
                "todos": [todo.model_dump(mode="json") for todo in todos],
            }
        )

    result_dict = await run_executor_agent(todos, config, on_todo_update=on_todo_update)
    result = result_dict.get("structured_response")
    messages = cast(list[BaseMessage], result_dict.get("messages", []))

    if result is None:
        return {
            "status": "failed",
            "messages": messages,
            "todos": todos,
            "issues": [
                *state["issues"],
                "El executor no devolvió una respuesta estructurada",
            ],
        }

    issues = [*state["issues"]]
    if result.status != "success":
        issues.append(result.recommendation or result.stop_reason)

    return {
        "status": result.status,
        "messages": messages,
        "todos": todos,
        "issues": issues,
    }


async def summary_node(state: GraphState, config: RunnableConfig) -> FinalReport:
    """Genera el reporte final usando el estado y la traza disponible."""

    writer = get_stream_writer()
    writer({"stage": "summarizing", "message": "Generando resumen"})

    prompt = _last_human_text(state["messages"])
    if not prompt:
        invalid_report: FinalReport = {
            "status": "invalid_request",
            "input": "",
            "interpretation": "No hay un mensaje humano en el historial para planificar.",
            "issues": state["issues"],
            "todos": [],
            "actions": [],
            "recommendation": "Enviar history con al menos un mensaje de tipo human.",
            "trace": [message_to_dict(message) for message in state["messages"]],
        }
        writer({"summary": invalid_report})
        return invalid_report

    result_dict = await run_summary_agent(
        cast(list[AnyMessage], state["messages"]), config
    )
    result = result_dict.get("structured_response")
    messages = cast(list[BaseMessage], result_dict.get("messages", []))[
        (len(state["messages"]) + 1) :
    ]
    if result is None:
        return _failure_report(
            prompt,
            RuntimeError("El summary no devolvió una respuesta estructurada"),
        )

    all_messages = [*state["messages"], *messages]
    report: FinalReport = {
        "status": state["status"] if state["status"] != "running" else result.status,
        "input": prompt,
        "interpretation": result.summary,
        "issues": state["issues"],
        "todos": [todo.model_dump() for todo in state["todos"]],
        "actions": [],
        "recommendation": result.recommendation,
        "trace": [message_to_dict(message) for message in all_messages],
    }
    writer({"summary": report})
    return report


async def _public_events(chunk: dict[str, object]) -> AsyncIterator[str]:
    if chunk.get("type") == "custom":
        data = cast(dict[str, object], chunk.get("data", {}))
        if "summary" in data:
            yield _sse("summary", data["summary"])
        elif "stage" in data:
            yield _sse("status", data)
        elif "todo_id" in data:
            yield _sse("todo", data)
        elif todos := data.get("todos"):
            yield _sse("todo", {"todos": todos})
        elif token := data.get("token"):
            yield _sse("token", token)
        elif reasoning := data.get("reasoning"):
            yield _sse("reasoning", reasoning)
        elif tool := data.get("tool"):
            yield _sse("tool", tool)
        return

    if chunk.get("type") == "messages":
        message, metadata = cast(tuple[BaseMessage, dict[str, object]], chunk["data"])
        agent = _agent_name(chunk, metadata)

        if isinstance(message, AIMessageChunk):
            if text := str(message.text):
                yield _sse("token", {"agent": agent, "content": text})
            if reasoning := _reasoning_text(message):
                yield _sse("reasoning", {"agent": agent, "content": reasoning})
            for tool_call in message.tool_call_chunks:
                if name := tool_call.get("name"):
                    yield _sse(
                        "tool",
                        {
                            "agent": agent,
                            "tool": name,
                            "status": "started",
                            "message": f"Invocando {name}",
                        },
                    )
            return

        if isinstance(message, ToolMessage):
            yield _sse(
                "tool",
                {
                    "agent": agent,
                    "tool": message.name or "tool",
                    "status": message.status,
                    "message": cast(str, message.content),
                },
            )


def _agent_name(chunk: dict[str, object], metadata: dict[str, object]) -> str:
    node = metadata.get("langgraph_node")
    if isinstance(node, str) and node != "model":
        return node

    ns = cast(tuple[str, ...], chunk.get("ns", ()))
    if ns:
        return ns[0].split(":", 1)[0]
    return str(node or "graph")


def _reasoning_text(message: AIMessageChunk) -> str:
    if reasoning := message.additional_kwargs.get("reasoning_content"):
        return cast(str, reasoning)

    parts: list[str] = []
    for block in message.content_blocks:
        if block.get("type") == "reasoning":
            text = block.get("reasoning") or block.get("text")
            if text:
                parts.append(str(text))
    return "".join(parts)


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _last_human_text(history: Sequence[BaseMessage]) -> str:
    for message in reversed(history):
        if isinstance(message, HumanMessage):
            return cast(str, message.content)
    return ""


def _failure_report(prompt: str, exc: Exception) -> FinalReport:
    return {
        "status": "failed",
        "input": prompt,
        "interpretation": "La ejecucion fallo antes de completar el flujo.",
        "issues": [f"{type(exc).__name__}: {exc}"],
        "todos": [],
        "actions": [],
        "recommendation": "Revisar el error y reintentar cuando el servicio este disponible.",
        "trace": [],
    }


builder = StateGraph(GraphState, output_schema=FinalReport)
_ = builder.add_node("planner", planner_node)
_ = builder.add_node("executor", executor_node)
_ = builder.add_node("summary", summary_node)
_ = builder.add_edge(START, "planner")
_ = builder.add_conditional_edges("planner", route_after_planner)
_ = builder.add_edge("executor", "summary")
_ = builder.add_edge("summary", END)
graph = builder.compile()


__all__ = [
    "FinalReport",
    "GraphState",
    "graph",
    "run_graph_json",
    "stream_graph_events",
]
