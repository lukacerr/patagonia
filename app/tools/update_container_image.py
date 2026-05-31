"""Tool mock para actualizar imagenes de servicios containerizados."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class UpdateContainerImageInput(BaseModel):
    """Input para actualizar una imagen container mockeada."""

    service_name: str = Field(description="Servicio objetivo")
    image: str = Field(description="Nueva imagen container")
    namespace: str = Field(description="Namespace del servicio")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def update_container_image(request: UpdateContainerImageInput) -> str:
    """Actualiza la imagen de un servicio containerizado simulado.

    Recibe service_name normalmente salido de deploy_container_service. Devuelve
    resource.type=container_service y resource.name=<service_name>.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "image_not_found", "La nueva imagen no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "rollout_timeout", "Timeout actualizando imagen", recoverable=True
        )

    return ok_response(
        "Imagen actualizada correctamente",
        resource={"type": "container_service", "name": request.service_name},
        details={"image": request.image, "namespace": request.namespace},
    )
