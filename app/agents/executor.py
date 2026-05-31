"""Agente executor: ejecuta TODOs usando exclusivamente tools mockeadas."""

import json
from collections.abc import Awaitable, Callable
from typing import Literal, cast

import toon
from langchain.agents import create_agent
from langchain.agents import AgentState
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agents.planner import PlannedTodo
from app.settings import settings
from app.tools import all_tools

SYSTEM_PROMPT = """Sos executorAgent, un Ingeniero DevOps Virtual que ejecuta planes.

Recibis TODOs planificados. Elegi y ejecuta tools disponibles para completar cada TODO.
No inventes resultados de tools. Las tools devuelven TOON: interpreta ok/error y recoverable.
Marca cada TODO como running, completed, retrying o failed usando mark_todo_status inmediatamente despues de cada cambio de estado.
Detene la ejecucion con estado claro si una tool devuelve un error no recuperable o si no podes completar el plan.

Ejecuta los TODOs recibidos en orden. Usa mark_todo_status para reportar progreso.
Cuando termines, devuelve ExecutorAgentResult.
"""


TodoStatus = Literal["running", "completed", "failed", "retrying"]


class ExecutorAgentResult(BaseModel):
    """Resultado final minimo del executor.

    Informa si el executor pudo completar el plan y por que se detuvo.
    """

    status: Literal["success", "partial", "failed"] = Field(
        description="Resultado global de ejecucion"
    )
    stop_reason: Literal[
        "completed",
        "unrecoverable_error",
        "retries_exhausted",
        "invalid_plan",
        "tool_not_found",
    ] = Field(description="Motivo final normalizado por enum")

    recommendation: str | None = Field(
        None, description="Siguiente paso recomendado luego de la ejecucion, si aplica"
    )


async def run_executor_agent(
    todos: list[PlannedTodo],
    config: RunnableConfig,
    *,
    on_todo_update: Callable[[str, TodoStatus], Awaitable[None]] | None = None,
) -> AgentState[ExecutorAgentResult]:
    """Ejecuta el plan en orden y reporta cambios de estado al grafo."""

    @tool
    async def mark_todo_status(todo_id: str, status: TodoStatus) -> str:
        """Marca el estado actual de un TODO para que el graph/frontend vea progreso.

        Usar inmediatamente cuando un TODO pasa a running, completed, retrying o failed.
        """

        if on_todo_update is not None:
            await on_todo_update(todo_id, status)

        return toon.encode({"ok": True, "todo_id": todo_id, "status": status})

    model = ChatOpenAI(
        model="zai-org/glm-5.1",
        api_key=settings.NOVITA_API_KEY,
        base_url=settings.NOVITA_BASE_URL,
        temperature=0,
        streaming=True,
    )
    agent = create_agent(
        model=model,
        tools=[*all_tools, mark_todo_status],
        system_prompt=SYSTEM_PROMPT,
        response_format=ExecutorAgentResult,
    )

    result = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=json.dumps(
                        [todo.model_dump(mode="json") for todo in todos],
                        ensure_ascii=False,
                    )
                )
            ]
        },
        config,
    )
    return cast(AgentState[ExecutorAgentResult], result)
