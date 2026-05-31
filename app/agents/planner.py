"""Agente planner: interpreta pedidos DevOps y produce TODOs seguros."""

from typing import Literal, cast

from langchain.agents import AgentState, create_agent
from collections.abc import Sequence

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.settings import settings
from app.tools import all_tools

SYSTEM_PROMPT = """Sos plannerAgent, un Ingeniero DevOps Virtual.

Tu unica tarea es interpretar el pedido, validar si hay datos suficientes y producir TODOs claros para un executor.
No ejecutes tools ni inventes datos faltantes. Usa la metadata de tools solo para entender capacidades disponibles.
Responde corto y directo. No uses markdown, backticks ni texto fuera del schema.
Responde siempre con el schema PlannerAgentResult.

Reglas importantes:
- Para pedidos ejecutables, status debe ser ready.
- No bloquees por nombres internos de recursos si pueden derivarse del contexto, por ejemplo servicio=pagos y ambiente=staging.
- Si el usuario dice 'nuevo developer', usa ese identificador como usuario suficiente.
- Bloquea solo si faltan datos realmente necesarios como engine, tamaño, recurso objetivo o permisos.
"""


class PlannedTodo(BaseModel):
    """Paso planificado por el planner.

    Describe una tarea que deberia realizar el executor. `relevant_args` lista
    datos importantes extraidos del pedido, por ejemplo `IP es 123.123.123.123`
    o `recurso objetivo es S3 mi-app`. No debe inventar datos faltantes.
    """

    id: str = Field(description="Identificador estable del TODO, por ejemplo todo_1")
    title: str = Field(description="Titulo corto y visible para UI/SSE")
    description: str = Field(description="Explicacion breve de lo que se va a hacer")
    done: bool = Field(False, description="Indica si el executor completo este TODO")
    depends_on: list[str] = Field(
        [], description="IDs de TODOs previos de los que depende este paso"
    )


class PlannerAgentResult(BaseModel):
    """Resultado estructurado del planner.

    `ready` significa que el grafo puede pasar al executor. `needs_input` corta
    ejecucion por datos faltantes. `invalid_request` corta ejecucion por una accion
    invalida o recurso inexistente evidente.
    """

    status: Literal["ready", "needs_input", "invalid_request"] = Field(
        description="Estado de planificacion"
    )
    interpretation: str = Field(
        description="Interpretacion breve y humana del pedido original"
    )
    missing_fields: list[str] = Field(
        [], description="Datos faltantes que impiden ejecutar con seguridad"
    )
    todos: list[PlannedTodo] = Field(
        [], description="Pasos ordenados para ejecutar si status=ready"
    )
    errors: list[str] = Field(
        [], description="Errores o bloqueos detectados al planificar"
    )


async def run_planner_agent(
    messages: Sequence[AnyMessage], config: RunnableConfig
) -> AgentState[PlannerAgentResult]:
    """Ejecuta el planner."""

    model = ChatOpenAI(
        model="openai/gpt-oss-120b",
        api_key=settings.NOVITA_API_KEY,
        base_url=settings.NOVITA_BASE_URL,
        temperature=0,
        streaming=True,
    )
    agent = create_agent(
        model=model,
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,
        response_format=PlannerAgentResult,
    )
    result = await agent.ainvoke(
        {"messages": [*messages]},
        config,
    )
    return cast(AgentState[PlannerAgentResult], result)
