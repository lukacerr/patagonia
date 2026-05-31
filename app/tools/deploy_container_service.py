"""Tool mock para desplegar servicios containerizados."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class DeployContainerServiceInput(BaseModel):
    """Input para desplegar un servicio containerizado mockeado."""

    service_name: str = Field(description="Nombre del servicio")
    image: str = Field(description="Imagen container a desplegar")
    namespace: str = Field(description="Namespace destino")
    replicas: int = Field(default=2, gt=0, description="Cantidad de replicas")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def deploy_container_service(request: DeployContainerServiceInput) -> str:
    """Despliega un servicio containerizado simulado.

    Devuelve resource.type=container_service y resource.name=<service_name>. Ese
    recurso puede encadenarse con configure_autoscaling o update_container_image.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "image_pull_failed",
            "La imagen no existe o no puede descargarse",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "deployment_timeout",
            "Timeout esperando rollout del servicio",
            recoverable=True,
        )

    return ok_response(
        "Servicio desplegado correctamente",
        resource={"type": "container_service", "name": request.service_name},
        details={
            "image": request.image,
            "namespace": request.namespace,
            "replicas": request.replicas,
        },
    )
