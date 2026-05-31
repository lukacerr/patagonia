"""Tool mock para ejecutar health checks de servicios o URLs."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class RunHealthCheckInput(BaseModel):
    """Input para ejecutar un health check mockeado."""

    target: str = Field(description="URL, servicio o recurso a validar")
    expected_status: int = Field(
        default=200, ge=100, le=599, description="Status esperado"
    )
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def run_health_check(request: RunHealthCheckInput) -> str:
    """Ejecuta un health check simulado.

    Devuelve resource.type=health_check y resource.name=<target>, con status
    esperado y observado en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "health_check_failed",
            "El health check devolvio un estado inesperado",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "health_check_timeout", "Timeout ejecutando health check", recoverable=True
        )

    return ok_response(
        "Health check exitoso",
        resource={"type": "health_check", "name": request.target},
        details={
            "expected_status": request.expected_status,
            "observed_status": request.expected_status,
        },
    )
