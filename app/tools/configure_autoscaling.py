"""Tool mock para configurar autoscaling de servicios."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class ConfigureAutoscalingInput(BaseModel):
    """Input para configurar autoscaling mockeado."""

    service_name: str = Field(description="Servicio objetivo")
    min_replicas: int = Field(gt=0, description="Minimo de replicas")
    max_replicas: int = Field(gt=0, description="Maximo de replicas")
    cpu_target_percent: int = Field(
        gt=0, le=100, description="CPU objetivo para escalar"
    )
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def configure_autoscaling(request: ConfigureAutoscalingInput) -> str:
    """Configura autoscaling simulado para un servicio.

    Recibe service_name normalmente salido de deploy_container_service. Devuelve
    resource.type=autoscaling_policy y resource.name=<service_name>.
    """

    await mock_delay()

    if request.max_replicas < request.min_replicas:
        return error_response(
            "invalid_autoscaling_range",
            "max_replicas debe ser mayor o igual a min_replicas",
            recoverable=False,
        )

    if request.failure_mode == "fatal_error":
        return error_response(
            "autoscaling_policy_denied",
            "La politica simulada no permite autoscaling",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "autoscaling_api_timeout",
            "Timeout configurando autoscaling",
            recoverable=True,
        )

    return ok_response(
        "Autoscaling configurado correctamente",
        resource={"type": "autoscaling_policy", "name": request.service_name},
        details={
            "min_replicas": request.min_replicas,
            "max_replicas": request.max_replicas,
            "cpu_target_percent": request.cpu_target_percent,
        },
    )
