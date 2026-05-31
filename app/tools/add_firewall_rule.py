"""Tool mock para agregar reglas de firewall a recursos existentes."""

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


KNOWN_RESOURCES = {
    ("s3_bucket", "payments-staging"),
    ("postgres_database", "payments-staging-db"),
}


class AddFirewallRuleInput(BaseModel):
    """Input para agregar una regla de firewall mockeada."""

    resource_type: Literal["s3_bucket", "postgres_database", "vpn"] = Field(
        description="Tipo de recurso objetivo"
    )
    resource_name: str = Field(description="Nombre del recurso objetivo")
    source_ip: str = Field(description="IP o CIDR a permitir")
    port: int | None = Field(
        default=None, gt=0, le=65535, description="Puerto opcional"
    )
    failure_mode: FailureMode = Field(
        default="random", description="Modo de fallo para demos/tests deterministas"
    )


@tool
async def add_firewall_rule(request: AddFirewallRuleInput) -> str:
    """Agrega una regla de firewall simulada sobre un recurso existente.

    Recibe resource_type/resource_name normalmente salidos de otra tool. Devuelve
    el mismo resource y details con source_ip y port.
    """

    await mock_delay()

    if (request.resource_type, request.resource_name) not in KNOWN_RESOURCES:
        return error_response(
            "resource_not_found",
            f"El recurso '{request.resource_name}' no existe en el inventario simulado",
            recoverable=False,
        )

    if request.failure_mode == "fatal_error":
        return error_response(
            "firewall_policy_denied",
            "La politica simulada no permite modificar este firewall",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "firewall_api_timeout",
            "Timeout al modificar firewall en API simulada",
            recoverable=True,
        )

    return ok_response(
        "Regla de firewall agregada correctamente",
        resource={"type": request.resource_type, "name": request.resource_name},
        details={"source_ip": request.source_ip, "port": request.port},
    )
