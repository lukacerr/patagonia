"""Adaptador HTTP de FastAPI para ejecutar el orquestador agentico."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AnyMessage
from scalar_fastapi import get_scalar_api_reference

from app.graph import run_graph_json, stream_graph_events
from app.settings import settings

app = FastAPI(
    title="IT Patagonia GenAI task",
    summary="API publica del Ingeniero DevOps Virtual.",
    description=(
        "Orquesta solicitudes DevOps en lenguaje natural mediante un grafo de "
        "planificacion, ejecucion simulada, observacion y resumen. Todas las "
        "integraciones externas son mocks locales; no provisiona cloud real."
    ),
    version="1.0.0",
    docs_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"]
    if settings.ENV == "development"
    else settings.CORS_ALLOW_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def scalar_html():
    """Renderiza Scalar como documentacion interactiva de OpenAPI."""

    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="IT Patagonia GenAI task API",
        scalar_proxy_url="https://proxy.scalar.com",
    )


@app.post(
    "/json",
    summary="Ejecutar orquestador y devolver JSON final",
    description=(
        "Recibe el historial de mensajes, ejecuta el ciclo planificar -> ejecutar "
        "-> resumir y devuelve un reporte estable para API, CLI y tests."
    ),
    response_description="Reporte final con estado, interpretacion, TODOs, issues y traza.",
)
async def run_json(payload: list[AnyMessage]):
    """Ejecuta el grafo completo y devuelve el reporte final serializable."""

    return await run_graph_json(payload)


@app.post(
    "/sse",
    summary="Ejecutar orquestador con stream SSE",
    description=(
        "Recibe el mismo historial que /json y emite eventos SSE de estado, "
        "TODOs, tokens, herramientas y resumen para mostrar progreso en tiempo real."
    ),
    response_description="Stream text/event-stream con eventos publicos del grafo.",
)
async def run_sse(payload: list[AnyMessage]):
    """Transmite eventos publicos del grafo usando Server-Sent Events."""

    return StreamingResponse(
        stream_graph_events(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
