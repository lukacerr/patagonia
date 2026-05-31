"""Tool mock para escalar deployments Kubernetes."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class ScaleKubernetesDeploymentInput(BaseModel):
    """Input para escalar un deployment Kubernetes mockeado."""

    deployment_name: str = Field(description="Deployment objetivo")
    namespace: str = Field(description="Namespace del deployment")
    replicas: int = Field(ge=0, description="Cantidad deseada de replicas")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def scale_kubernetes_deployment(request: ScaleKubernetesDeploymentInput) -> str:
    """Escala un deployment Kubernetes simulado.

    Devuelve resource.type=kubernetes_deployment y resource.name=<deployment_name>,
    con namespace y replicas en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "deployment_not_found", "El deployment no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "scale_timeout", "Timeout escalando deployment", recoverable=True
        )

    return ok_response(
        "Deployment escalado correctamente",
        resource={"type": "kubernetes_deployment", "name": request.deployment_name},
        details={"namespace": request.namespace, "replicas": request.replicas},
    )
