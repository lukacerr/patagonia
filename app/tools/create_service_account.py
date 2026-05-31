"""Tool mock para crear service accounts de aplicacion o plataforma."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class CreateServiceAccountInput(BaseModel):
    """Input para crear una service account mockeada."""

    account_name: str = Field(description="Nombre de la service account")
    namespace: str | None = Field(default=None, description="Namespace si aplica")
    owner: str = Field(description="Equipo responsable")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_service_account(request: CreateServiceAccountInput) -> str:
    """Crea una service account simulada.

    Devuelve resource.type=service_account y resource.name=<account_name>. Ese
    principal puede encadenarse con grant_iam_role.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "service_account_already_exists",
            "La service account ya existe",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "identity_api_timeout", "Timeout creando service account", recoverable=True
        )

    return ok_response(
        "Service account creada correctamente",
        resource={"type": "service_account", "name": request.account_name},
        details={"namespace": request.namespace, "owner": request.owner},
    )
