"""Agente summary: sintetiza el run completo sin inventar resultados."""

from collections.abc import Sequence
from typing import Literal, TypedDict, cast

from langchain.agents import AgentState, create_agent
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.settings import settings


class AgentInputState(TypedDict):
    """Input minimo esperado por create_agent para el summary."""

    messages: list[AnyMessage | dict[str, object]]


SYSTEM_PROMPT = """Sos summaryAgent, un Ingeniero DevOps Virtual que resume ejecuciones.

Recibis el historial completo del run preparado por el grafo. No inventes run_id, acciones ni resultados de tools.
Resume de forma clara, amable y factual en maximo dos frases. No ocultes errores ni causas. No filtres secretos.
Responde siempre con SummaryAgentResult.
"""


class SummaryAgentResult(BaseModel):
    """Resumen narrativo y recomendacion final generados por el LLM.

    No debe inventar datos del run. Solo sintetiza el historial recibido y propone
    una recomendacion si hay un siguiente paso claro.
    """

    status: Literal[
        "success", "partial", "failed", "needs_input", "invalid_request"
    ] = Field(description="Estado final interpretado desde el historial recibido")
    summary: str = Field(
        description="Resumen breve de maximo dos frases sobre lo ocurrido"
    )
    recommendation: str | None = Field(
        None, description="Siguiente paso recomendado para el usuario, si aplica"
    )


async def run_summary_agent(
    messages: Sequence[AnyMessage], config: RunnableConfig
) -> AgentState[SummaryAgentResult]:
    """Genera un resumen final tomando el historial como unica fuente de verdad."""

    model = ChatOpenAI(
        model="openai/gpt-oss-120b",
        api_key=settings.NOVITA_API_KEY,
        base_url=settings.NOVITA_BASE_URL,
        temperature=0,
        streaming=True,
    )
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        response_format=SummaryAgentResult,
    )
    input_messages: list[AnyMessage] = [
        *messages,
        HumanMessage(
            content="Genera el reporte final usando la conversacion anterior como fuente de verdad. No inventes acciones ni resultados."
        ),
    ]
    input_state: AgentInputState = {"messages": [*input_messages]}
    result = await agent.ainvoke(
        input_state,
        config,
    )
    return cast(AgentState[SummaryAgentResult], result)
