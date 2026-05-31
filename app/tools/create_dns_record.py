"""Tool mock para crear registros DNS en zonas simuladas."""

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


class CreateDnsRecordInput(BaseModel):
    """Input para crear un registro DNS mockeado."""

    zone: str = Field(description="Zona DNS")
    name: str = Field(description="Nombre del registro")
    record_type: Literal["A", "AAAA", "CNAME", "TXT"] = Field(
        description="Tipo de registro"
    )
    value: str = Field(description="Valor del registro")
    ttl_seconds: int = Field(default=300, gt=0, description="TTL en segundos")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_dns_record(request: CreateDnsRecordInput) -> str:
    """Crea un registro DNS simulado.

    Devuelve resource.type=dns_record y resource.name=<name>, con zone,
    record_type, value y ttl_seconds en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "dns_zone_not_found",
            "La zona DNS no existe en el inventario simulado",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "dns_api_timeout", "Timeout creando registro DNS", recoverable=True
        )

    return ok_response(
        "Registro DNS creado correctamente",
        resource={"type": "dns_record", "name": request.name},
        details={
            "zone": request.zone,
            "record_type": request.record_type,
            "value": request.value,
            "ttl_seconds": request.ttl_seconds,
        },
    )
