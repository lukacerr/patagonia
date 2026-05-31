"""Tool mock para crear buckets S3 privados o publicos."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class CreateS3BucketInput(BaseModel):
    """Input para crear un bucket S3 mockeado."""

    bucket_name: str = Field(description="Nombre unico del bucket S3 a crear")
    environment: str = Field(description="Ambiente objetivo, por ejemplo staging")
    private: bool = Field(default=True, description="Si el bucket debe ser privado")
    owner: str | None = Field(default=None, description="Equipo o servicio responsable")
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def create_s3_bucket(request: CreateS3BucketInput) -> str:
    """Crea un bucket S3 simulado con configuracion de privacidad.

    Devuelve resource.type=s3_bucket y resource.name=<bucket_name>. Ese recurso
    puede encadenarse con tools como add_firewall_rule.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "invalid_bucket_name",
            "El nombre del bucket no cumple las reglas simuladas",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "s3_api_timeout",
            "Timeout al crear bucket S3 en API simulada",
            recoverable=True,
        )

    return ok_response(
        "Bucket S3 creado correctamente",
        resource={"type": "s3_bucket", "name": request.bucket_name},
        details={
            "environment": request.environment,
            "private": request.private,
            "owner": request.owner,
        },
    )
