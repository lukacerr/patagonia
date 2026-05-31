"""Tool mock para configurar politicas de retencion de logs."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class CreateLogRetentionPolicyInput(BaseModel):
    """Input para crear politica de retencion de logs mockeada."""

    log_group: str = Field(description="Grupo de logs objetivo")
    retention_days: int = Field(gt=0, description="Dias de retencion")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_log_retention_policy(request: CreateLogRetentionPolicyInput) -> str:
    """Configura retencion de logs simulada.

    Devuelve resource.type=log_group y resource.name=<log_group>, con
    retention_days en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "log_group_not_found", "El grupo de logs no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "logging_api_timeout", "Timeout configurando retencion", recoverable=True
        )

    return ok_response(
        "Politica de retencion de logs configurada correctamente",
        resource={"type": "log_group", "name": request.log_group},
        details={"retention_days": request.retention_days},
    )
