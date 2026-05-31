"""Tool mock para crear alertas de monitoreo con severidad y canal."""

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


class CreateMonitoringAlertInput(BaseModel):
    """Input para crear una alerta de monitoreo mockeada."""

    alert_name: str = Field(description="Nombre de la alerta")
    metric: str = Field(description="Metrica monitoreada")
    threshold: float = Field(description="Umbral de disparo")
    severity: Literal["info", "warning", "critical"] = Field(description="Severidad")
    notify_channel: str = Field(description="Canal de notificacion")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def create_monitoring_alert(request: CreateMonitoringAlertInput) -> str:
    """Crea una alerta de monitoreo simulada.

    Devuelve resource.type=monitoring_alert y resource.name=<alert_name>, con
    metric, threshold, severity y notify_channel en details.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "notification_channel_not_found",
            "El canal de notificacion no existe",
            recoverable=False,
        )

    if should_fail(request.failure_mode):
        return error_response(
            "monitoring_api_timeout", "Timeout creando alerta", recoverable=True
        )

    return ok_response(
        "Alerta de monitoreo creada correctamente",
        resource={"type": "monitoring_alert", "name": request.alert_name},
        details={
            "metric": request.metric,
            "threshold": request.threshold,
            "severity": request.severity,
            "notify_channel": request.notify_channel,
        },
    )
