"""Tool mock para reiniciar servicios por ambiente."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class RestartServiceInput(BaseModel):
    """Input para reiniciar un servicio mockeado."""

    service_name: str = Field(description="Servicio a reiniciar")
    environment: str = Field(description="Ambiente del servicio")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def restart_service(request: RestartServiceInput) -> str:
    """Reinicia un servicio simulado.

    Devuelve resource.type=service y resource.name=<service_name>, con environment
    en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "service_not_found", "El servicio no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "restart_timeout", "Timeout reiniciando servicio", recoverable=True
        )

    return ok_response(
        "Servicio reiniciado correctamente",
        resource={"type": "service", "name": request.service_name},
        details={"environment": request.environment},
    )
