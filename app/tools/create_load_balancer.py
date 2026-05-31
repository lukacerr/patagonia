"""Tool mock para crear load balancers publicos o privados."""

from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class CreateLoadBalancerInput(BaseModel):
    """Input para crear un load balancer mockeado."""

    name: str = Field(description="Nombre del load balancer")
    target_service: str = Field(description="Servicio backend objetivo")
    visibility: Literal["public", "private"] = Field(
        description="Visibilidad del balanceador"
    )
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_load_balancer(request: CreateLoadBalancerInput) -> str:
    """Crea un load balancer simulado para un servicio.

    Recibe target_service normalmente salido de deploy_container_service. Devuelve
    resource.type=load_balancer y resource.name=<name>.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "load_balancer_limit_reached",
            "Limite simulado de load balancers alcanzado",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "load_balancer_api_timeout",
            "Timeout creando load balancer",
            recoverable=True,
        )

    return ok_response(
        "Load balancer creado correctamente",
        resource={"type": "load_balancer", "name": request.name},
        details={
            "target_service": request.target_service,
            "visibility": request.visibility,
        },
    )
