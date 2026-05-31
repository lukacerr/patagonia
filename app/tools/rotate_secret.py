"""Tool mock para rotar secretos sin exponer valores sensibles."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class RotateSecretInput(BaseModel):
    """Input para rotar un secreto mockeado."""

    secret_name: str = Field(description="Nombre del secreto")
    owner: str = Field(description="Equipo responsable")
    notify: bool = Field(default=True, description="Si debe notificarse al owner")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def rotate_secret(request: RotateSecretInput) -> str:
    """Rota un secreto simulado sin exponer su valor.

    Devuelve resource.type=secret y resource.name=<secret_name>. El valor del
    secreto nunca se expone; details.secret_value siempre es redacted.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "secret_not_found",
            "El secreto no existe en el store simulado",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "secrets_api_timeout", "Timeout rotando secreto", recoverable=True
        )

    return ok_response(
        "Secreto rotado correctamente",
        resource={"type": "secret", "name": request.secret_name},
        details={
            "owner": request.owner,
            "notify": request.notify,
            "secret_value": "redacted",
        },
    )
