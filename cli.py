"""CLI del orquestador que reutiliza el mismo contrato JSON de la API."""

import asyncio
import json

import typer
from langchain_core.messages import HumanMessage

from app.graph import run_graph_json


def main(prompt: str):
    """Ejecuta una solicitud DevOps en lenguaje natural desde terminal."""

    result = asyncio.run(run_graph_json([HumanMessage(content=prompt)]))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


typer.run(main)
