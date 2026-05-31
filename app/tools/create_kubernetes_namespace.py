"""Tool mock para crear namespaces Kubernetes en clusters simulados."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class CreateKubernetesNamespaceInput(BaseModel):
    """Input para crear un namespace Kubernetes mockeado."""

    namespace: str = Field(description="Nombre del namespace")
    cluster: str = Field(description="Cluster Kubernetes destino")
    owner: str = Field(description="Equipo responsable")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_kubernetes_namespace(request: CreateKubernetesNamespaceInput) -> str:
    """Crea un namespace Kubernetes simulado.

    Devuelve resource.type=kubernetes_namespace y resource.name=<namespace>. Ese
    name puede usarse como namespace para deploy_container_service.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "namespace_already_exists",
            "El namespace ya existe en el cluster simulado",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "kubernetes_api_timeout", "Timeout al crear namespace", recoverable=True
        )

    return ok_response(
        "Namespace Kubernetes creado correctamente",
        resource={"type": "kubernetes_namespace", "name": request.namespace},
        details={"cluster": request.cluster, "owner": request.owner},
    )
