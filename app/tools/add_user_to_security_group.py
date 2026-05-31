"""Tool mock para asignar usuarios a grupos de seguridad conocidos."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


KNOWN_SECURITY_GROUPS = {"backend-devs", "data-science", "platform-admins"}


class AddUserToSecurityGroupInput(BaseModel):
    """Input para agregar un usuario a un grupo de seguridad mockeado."""

    user: str = Field(description="Usuario, email o identificador de persona")
    group_name: str = Field(description="Nombre del grupo de seguridad")
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def add_user_to_security_group(
    request: AddUserToSecurityGroupInput,
) -> str:
    """Agrega un usuario a un grupo de seguridad simulado.

    Devuelve resource.type=security_group y resource.name=<group_name>, con el
    usuario afectado en details.user.
    """

    await mock_delay()

    if request.group_name not in KNOWN_SECURITY_GROUPS:
        return error_response(
            "security_group_not_found",
            f"El grupo de seguridad '{request.group_name}' no existe en el inventario simulado",
            recoverable=False,
        )

    if request.failure_mode == "fatal_error":
        return error_response(
            "identity_policy_denied",
            "La politica simulada no permite modificar este grupo",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "identity_api_timeout",
            "Timeout al actualizar grupo de seguridad en API simulada",
            recoverable=True,
        )

    return ok_response(
        "Usuario agregado al grupo de seguridad correctamente",
        resource={"type": "security_group", "name": request.group_name},
        details={"user": request.user},
    )
