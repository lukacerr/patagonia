"""Tool mock para habilitar acceso VPN temporal a usuarios."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class EnableVpnAccessInput(BaseModel):
    """Input para habilitar acceso VPN mockeado."""

    user: str = Field(description="Usuario, email o identificador de persona")
    environment: str = Field(default="corporate", description="Ambito de acceso VPN")
    duration_days: int = Field(
        default=90, gt=0, description="Duracion del acceso en dias"
    )
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def enable_vpn_access(request: EnableVpnAccessInput) -> str:
    """Habilita acceso VPN simulado para un usuario.

    Devuelve resource.type=vpn_access y resource.name=<user>. Puede encadenarse
    con add_user_to_security_group usando el mismo usuario.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "vpn_policy_denied",
            "La politica simulada no permite habilitar VPN para este usuario",
            recoverable=False,
        )

    if should_fail(request.failure_mode, chance=0.12):
        return error_response(
            "network_timeout",
            "Timeout al llamar la API simulada de VPN",
            recoverable=True,
        )

    return ok_response(
        "Acceso VPN habilitado correctamente",
        resource={"type": "vpn_access", "name": request.user},
        details={
            "environment": request.environment,
            "duration_days": request.duration_days,
        },
    )
