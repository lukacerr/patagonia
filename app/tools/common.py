"""Utilidades compartidas por las tools mockeadas del dominio DevOps."""

import asyncio
import random
from typing import Literal

import toon


FailureMode = Literal["random", "success", "recoverable_error", "fatal_error"]


async def mock_delay() -> None:
    """Simula latencia de una integracion externa sin llamar servicios reales."""

    await asyncio.sleep(random.uniform(0.5, 5.0))


def should_fail(failure_mode: FailureMode, chance: float = 0.08) -> bool:
    """Evalua si una tool debe fallar segun modo determinista o azar controlado."""

    return failure_mode == "recoverable_error" or (
        failure_mode == "random" and random.random() < chance
    )


def ok_response(
    message: str,
    resource: dict[str, object] | None = None,
    details: dict[str, object] | None = None,
) -> str:
    """Codifica una respuesta exitosa de tool usando el envelope TOON estable."""

    return toon.encode(
        {
            "ok": True,
            "message": message,
            "resource": resource or {},
            "details": details or {},
        }
    )


def error_response(
    code: str,
    message: str,
    *,
    recoverable: bool,
) -> str:
    """Codifica un error de tool con codigo, mensaje y recuperabilidad."""

    return toon.encode(
        {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "recoverable": recoverable,
            },
        }
    )
