"""Tool mock para ejecutar backups de bases de datos."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.tools.common import (
    FailureMode,
    error_response,
    mock_delay,
    ok_response,
    should_fail,
)


class RunDatabaseBackupInput(BaseModel):
    """Input para ejecutar un backup de base de datos mockeado."""

    database_name: str = Field(description="Base de datos objetivo")
    backup_label: str = Field(description="Etiqueta del backup")
    failure_mode: FailureMode = Field(default="random", description="Modo de fallo")


@tool
async def run_database_backup(request: RunDatabaseBackupInput) -> str:
    """Ejecuta un backup simulado de una base de datos.

    Recibe database_name normalmente salido de create_postgres_database. Devuelve
    resource.type=database_backup y resource.name=<backup_label>.
    """

    await mock_delay()

    if request.failure_mode == "fatal_error":
        return error_response(
            "database_not_found", "La base de datos no existe", recoverable=False
        )

    if should_fail(request.failure_mode):
        return error_response(
            "backup_timeout", "Timeout ejecutando backup", recoverable=True
        )

    return ok_response(
        "Backup ejecutado correctamente",
        resource={"type": "database_backup", "name": request.backup_label},
        details={"database_name": request.database_name},
    )
