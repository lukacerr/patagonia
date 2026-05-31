"""Tool mock para aplicar planes Terraform aprobados."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class ApplyTerraformPlanInput(BaseModel):
    """Input para aplicar un plan Terraform mockeado."""

    workspace: str = Field(description="Workspace de Terraform")
    plan_id: str = Field(description="Identificador del plan aprobado")
    auto_approve: bool = Field(
        default=False, description="Si se aplica sin aprobacion manual"
    )
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def apply_terraform_plan(request: ApplyTerraformPlanInput) -> str:
    """Aplica un plan Terraform simulado.

    Devuelve resource.type=terraform_workspace y resource.name=<workspace>, con
    plan_id en details. Requiere auto_approve=True.
    """

    await mock_delay()

    if not request.auto_approve:
        return error_response(
            "approval_required",
            "El plan requiere aprobacion explicita antes de aplicar",
            recoverable=False,
        )

    if request.failure_mode == "fatal_error":
        return error_response(
            "terraform_plan_invalid",
            "El plan Terraform simulado no es valido",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "terraform_apply_timeout",
            "Timeout aplicando plan Terraform",
            recoverable=True,
        )

    return ok_response(
        "Plan Terraform aplicado correctamente",
        resource={"type": "terraform_workspace", "name": request.workspace},
        details={"plan_id": request.plan_id},
    )
