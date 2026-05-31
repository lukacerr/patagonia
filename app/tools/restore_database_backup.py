"""Tool mock para restaurar backups en bases de datos destino."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class RestoreDatabaseBackupInput(BaseModel):
    """Input para restaurar un backup mockeado."""

    backup_label: str = Field(description="Backup a restaurar")
    target_database_name: str = Field(description="Base destino")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def restore_database_backup(request: RestoreDatabaseBackupInput) -> str:
    """Restaura un backup de base de datos simulado.

    Recibe backup_label normalmente salido de run_database_backup. Devuelve
    resource.type=postgres_database y resource.name=<target_database_name>.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "backup_not_found", "El backup no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "restore_timeout", "Timeout restaurando backup", recoverable=True
        )

    return ok_response(
        "Backup restaurado correctamente",
        resource={"type": "postgres_database", "name": request.target_database_name},
        details={"backup_label": request.backup_label},
    )
