"""Tool mock para provisionar bases PostgreSQL con tamano definido."""

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


class CreatePostgresDatabaseInput(BaseModel):
    """Input para crear una base PostgreSQL mockeada."""

    database_name: str = Field(description="Nombre de la base de datos")
    environment: str = Field(description="Ambiente objetivo, por ejemplo staging")
    size_gb: int = Field(gt=0, description="Tamano de la base en GB")
    owner: str = Field(description="Equipo o servicio responsable")
    engine: Literal["postgresql"] = Field(
        default="postgresql", description="Motor requerido"
    )
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def create_postgres_database(
    request: CreatePostgresDatabaseInput,
) -> str:
    """Crea una base PostgreSQL simulada con tamano y owner definidos.

    Devuelve resource.type=postgres_database y resource.name=<database_name>.
    Ese recurso puede usarse luego para backups, restores o firewall.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "database_quota_exceeded",
            "La cuota simulada no permite crear esta base de datos",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "database_api_timeout",
            "Timeout al crear base PostgreSQL en API simulada",
            recoverable=True,
        )

    return ok_response(
        "Base PostgreSQL creada correctamente",
        resource={"type": "postgres_database", "name": request.database_name},
        details={
            "environment": request.environment,
            "size_gb": request.size_gb,
            "owner": request.owner,
            "engine": request.engine,
        },
    )
