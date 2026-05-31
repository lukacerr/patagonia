"""Tool mock para validar recursos contra un inventario local."""

from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
)


RESOURCE_INVENTORY = {
    ("s3_bucket", "payments-staging"),
    ("postgres_database", "payments-staging-db"),
    ("security_group", "backend-devs"),
    ("security_group", "data-science"),
    ("security_group", "platform-admins"),
}


class ValidateResourceExistsInput(BaseModel):
    """Input para validar existencia de recursos mockeados."""

    resource_type: Literal[
        "s3_bucket", "postgres_database", "security_group", "vpn"
    ] = Field(description="Tipo de recurso a validar")
    resource_name: str = Field(description="Nombre del recurso a validar")
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def validate_resource_exists(
    request: ValidateResourceExistsInput,
) -> str:
    """Valida si un recurso existe en el inventario simulado.

    Devuelve resource.type=<resource_type> y resource.name=<resource_name> si el
    recurso existe. En error resource_not_found no debe continuarse la ejecucion.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "inventory_unavailable",
            "El inventario simulado no esta disponible",
            recoverable=True,
        )

    exists = (request.resource_type, request.resource_name) in RESOURCE_INVENTORY
    if not exists:
        return error_response(
            "resource_not_found",
            f"El recurso '{request.resource_name}' no existe en el inventario simulado",
            recoverable=False,
        )

    return ok_response(
        "Recurso encontrado en inventario simulado",
        resource={"type": request.resource_type, "name": request.resource_name},
    )
