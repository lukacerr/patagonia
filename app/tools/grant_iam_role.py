"""Tool mock para otorgar roles IAM a principals simulados."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class GrantIamRoleInput(BaseModel):
    """Input para otorgar un rol IAM mockeado."""

    principal: str = Field(description="Usuario, grupo o service account")
    role: str = Field(description="Rol IAM a otorgar")
    resource_scope: str = Field(description="Alcance del permiso")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def grant_iam_role(request: GrantIamRoleInput) -> str:
    """Otorga un rol IAM simulado a un principal.

    Recibe principal normalmente salido de create_service_account. Devuelve
    resource.type=iam_binding y resource.name=<principal>.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "iam_policy_denied",
            "La politica simulada no permite otorgar ese rol",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "iam_api_timeout", "Timeout otorgando rol IAM", recoverable=True
        )

    return ok_response(
        "Rol IAM otorgado correctamente",
        resource={"type": "iam_binding", "name": request.principal},
        details={"role": request.role, "resource_scope": request.resource_scope},
    )
