"""Tool mock para crear caches Redis por ambiente y owner."""

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


class CreateRedisCacheInput(BaseModel):
    """Input para crear un cache Redis mockeado."""

    cache_name: str = Field(description="Nombre del cluster Redis")
    environment: str = Field(description="Ambiente objetivo")
    size: Literal["small", "medium", "large"] = Field(description="Tamano del cache")
    owner: str = Field(description="Equipo responsable")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_redis_cache(request: CreateRedisCacheInput) -> str:
    """Crea un cache Redis simulado para una aplicacion.

    Devuelve resource.type=redis_cache y resource.name=<cache_name>, con
    environment, size y owner en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "redis_quota_exceeded",
            "No hay cuota simulada para crear Redis",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "redis_api_timeout",
            "Timeout al crear Redis en API simulada",
            recoverable=True,
        )

    return ok_response(
        "Cache Redis creado correctamente",
        resource={"type": "redis_cache", "name": request.cache_name},
        details={
            "environment": request.environment,
            "size": request.size,
            "owner": request.owner,
        },
    )
