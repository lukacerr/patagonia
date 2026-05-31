"""Tool mock para purgar paths en distribuciones CDN."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class PurgeCdnCacheInput(BaseModel):
    """Input para purgar cache CDN mockeado."""

    distribution: str = Field(description="Distribucion CDN")
    paths: list[str] = Field(description="Paths a invalidar")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def purge_cdn_cache(request: PurgeCdnCacheInput) -> str:
    """Purga cache CDN simulado para paths especificos.

    Devuelve resource.type=cdn_distribution y resource.name=<distribution>, con
    los paths invalidados en details.paths.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "cdn_distribution_not_found",
            "La distribucion CDN no existe",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "cdn_api_timeout", "Timeout purgando cache CDN", recoverable=True
        )

    return ok_response(
        "Cache CDN purgado correctamente",
        resource={"type": "cdn_distribution", "name": request.distribution},
        details={"paths": request.paths},
    )
