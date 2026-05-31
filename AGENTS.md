# AGENTS.md

## Mision

Este repositorio implementa la prueba tecnica de un orquestador agentico en Python para el dominio "Ingeniero DevOps Virtual".

El sistema recibe requerimientos en lenguaje natural para provisionar infraestructura cloud o ejecutar tareas DevOps, interpreta la intencion con IA, planifica pasos, ejecuta acciones simuladas, observa resultados, decide reintentos o interrupciones y deja trazabilidad clara de todo lo ocurrido.

El foco del challenge es planificacion, ejecucion, manejo de errores, trazabilidad y comunicacion. No construir un chatbot generico ni conectar servicios cloud reales.

## Stack Y Restricciones

- Backend: Python, FastAPI, LangChain, LangGraph, Pydantic y Typer.
- Tool responses: usar strings en formato TOON con `python-toon` para entregar resultados compactos y faciles de consumir por agentes.
- LLM provider: Novita AI via API compatible con OpenAI.
- Planner y summary: `openai/gpt-oss-120b`.
- Executor: `zai-org/glm-5.1`.
- Web: Astro estatico, sin SSR ni islands, deployable en Cloudflare Pages.
- API publica esperada: `https://patagonia.luka.software`.
- Usar async de punta a punta cuando las librerias lo permitan.
- Todas las integraciones externas deben ser mocks locales; no llamar APIs cloud reales.
- No filtrar secretos del `.env` en logs, errores, trazas, SSE ni reportes.

## Arquitectura Acordada

La estructura principal queda definida asi:

- `app/agents/planner.py`: system prompt, inicializacion y funcion async `run_planner_agent(...)` con return type especifico.
- `app/agents/executor.py`: system prompt, inicializacion y funcion async `run_executor_agent(...)` con return type especifico.
- `app/agents/summary.py`: system prompt, inicializacion y funcion async `run_summary_agent(...)` con return type especifico.
- `app/tools/`: tools mockeadas simples, decoradas con `@tool` de LangChain, con descripcion clara e inputs tipados con Pydantic.
- `app/tools/__init__.py`: exporta `all_tools = [...]` para bindear facilmente en el executor y metadata simple de tools para que el planner conozca nombres, descripciones y schemas sin poder ejecutarlas.
- `app/graph.py`: contiene el `TypedDict` del estado, la logica de LangGraph y exporta el grafo.
- `app/main.py`: adaptador FastAPI delgado que importa el grafo y expone `POST /json` y `POST /sse`.
- `cli.py`: adaptador Typer delgado que importa el grafo y devuelve lo mismo que `POST /json`.
- `tests/`: escenarios ejecutables con `pytest` y `pytest-asyncio`; al inicio sirven para imprimir outputs y evaluar calidad manualmente, no para bloquear con asserts fuertes.

Mantener nombres Python en `snake_case`. Evitar introducir capas adicionales si no reducen codigo o complejidad real.

## Flujo Del Grafo

El grafo debe representar el ciclo agentico: planificar -> ejecutar -> observar -> decidir -> resumir.

1. `plannerAgent` recibe el pedido original, interpreta la intencion, valida si hay datos suficientes y produce una lista de TODOs ejecutables.
2. Si faltan datos, hay ambiguedad bloqueante o se referencia un recurso inexistente, no se ejecutan herramientas y se pasa directo a `summaryAgent`.
3. Si el pedido es ejecutable, `executorAgent` recibe el plan y ejecuta los TODOs en orden.
4. Cada accion debe actualizar su estado a medida que avanza.
5. Si una accion falla por un error recuperable, el sistema debe hacer reintentos acotados y registrar la decision.
6. Si el error persiste o no es recuperable, la ejecucion termina con estado claro: `partial` o `failed` segun corresponda.
7. `summaryAgent` genera el reporte final usando todo el contexto disponible.

## Endpoints Y CLI

- `POST /json`: recibe un prompt y devuelve el resumen JSON completo de la ejecucion.
- `POST /sse`: recibe el mismo input y devuelve un stream estilo SSE con lo que va pasando en tiempo real.
- `cli.py`: debe exponer el mismo comportamiento que `POST /json`.
- `/json` y `/sse` deben protegerse con API key usando header en FastAPI.

Los endpoints y la CLI deben ser adaptadores finos. La logica del orquestador debe vivir fuera de ellos para poder reutilizarla y testearla.

## Contrato De Entrada

La entrada minima es texto simple. Para HTTP puede envolverse en JSON:

```json
{
  "prompt": "Necesito que levantes un entorno de staging..."
}
```

## Contrato De Salida JSON

El reporte final debe ser estable para API, CLI y tests.

```json
{
  "run_id": "...",
  "status": "success|partial|failed|needs_input|invalid_request",
  "input": "...",
  "interpretation": {},
  "missing_fields": [],
  "todos": [],
  "actions": [],
  "errors": [],
  "recommendation": "...",
  "trace": []
}
```

`status` debe reflejar el estado real:

- `success`: todo se ejecuto correctamente.
- `partial`: algunas acciones se completaron y otra fallo de forma definitiva.
- `failed`: no se pudo completar ninguna accion relevante por error de ejecucion.
- `needs_input`: faltan datos para planificar con seguridad.
- `invalid_request`: el pedido referencia recursos inexistentes o pide una accion invalida.

## Eventos SSE

La taxonomia debe ser simple de implementar en el front y contener informacion suficiente para mostrar el progreso en tiempo real.

Formato recomendado:

```text
event: status
data: {"run_id":"...","stage":"planning","message":"Interpretando solicitud"}

event: todo
data: {"id":"...","title":"Crear bucket S3 privado","status":"running","message":"Ejecutando accion"}

event: action
data: {"id":"...","tool":"create_s3_bucket","status":"completed","attempt":1,"message":"Bucket creado"}

event: error
data: {"code":"network_timeout","recoverable":true,"message":"Timeout al llamar API simulada"}

event: summary
data: {"status":"partial","recommendation":"Reintentar alta VPN mas tarde"}
```

Mantener pocos tipos de evento. Preferir payloads JSON claros antes que nombres de evento demasiado especificos.

Como el endpoint es `POST /sse`, la web debe consumirlo con `fetch` y lectura del stream, no con `EventSource`.

## Herramientas Mockeadas

Las herramientas externas representan APIs de cloud, red o seguridad, pero deben ser completamente simuladas.

Ejemplos de capacidades:

- Crear bucket S3 privado.
- Crear base de datos PostgreSQL con tamano definido.
- Habilitar acceso VPN.
- Agregar usuario a grupo de seguridad.
- Modificar reglas de firewall.
- Validar existencia de recursos en un inventario local.

Los mocks pueden tener fallos capciosos o aleatorios para demo manual, pero los tests deben poder forzar resultados deterministas mediante seed, escenario o inyeccion simple de dependencias.

Las tools deben importar el decorator oficial de LangChain, por ejemplo `from langchain_core.tools import tool`. Evitar wrappers propios salvo que agreguen valor real.

Las tools deben devolver `str` en formato TOON, no dicts Python crudos. Mantener un envelope estable dentro del TOON: `ok`, `message`, `resource`, `details` para exito; `ok` y `error` para fallos. Documentar en la docstring que `resource.type` y `resource.name` pueden usarse para encadenar tools.

## Escenarios Obligatorios

Estos escenarios deben quedar cubiertos mas adelante con `pytest` y `pytest-asyncio`.

1. Happy path: "Necesito que levantes un entorno de staging para el nuevo microservicio de pagos. Vas a tener que crear un bucket de S3 privado y una base de datos PostgreSQL de 50GB."
2. Falta de informacion: "Deploya una nueva base de datos para el equipo de Data Science, por favor."
3. Falla de integracion: "Habilita el acceso VPN para el nuevo developer y agregalo al grupo de seguridad 'backend-devs'."
4. Informacion erronea: "Agrega la ip 123.123.123.123 al firewall del S3 'mi-app'."

Los tests iniciales pueden imprimir outputs para evaluacion manual usando `pytest -s`. Evitar asserts fuertes hasta que la calidad de las respuestas este estabilizada, pero conservar determinismo suficiente para reproducir escenarios.

## Criterios De Implementacion

- No inventar datos faltantes. Si falta engine, tamano, entorno, permisos, recurso objetivo u otro dato necesario, interrumpir y reportarlo.
- Priorizar codigo corto, directo y facil de seguir. Evitar dedicar demasiadas lineas a cosas que pueden resolverse de forma mas simple.
- Mantener trazabilidad de interpretacion, plan, acciones, resultados, errores, reintentos y decisiones.
- Los errores deben comunicarse de forma clara y amable al usuario, sin ocultar la causa.
- Los TODOs deben poder verse en la web mientras se ejecutan.
- La web debe ser estatica y consumir la API remota `https://patagonia.luka.software`.
- El README corto se escribira hacia el final, cuando la implementacion este cerrada.
- Si `basedpyright` falla por warnings claramente originados en typings externos de librerias, preferir configurar el warning en `pyproject.toml` antes que crear wrappers o casts artificiales en codigo de negocio.
- Evitar clientes async globales de LLM a nivel modulo; crear modelos por llamada o mediante factory para no atarlos al event loop de pytest/FastAPI.
- Despues de cambios o correcciones relevantes, evaluar si `AGENTS.md` deberia actualizarse con una nueva regla aprendida para futuras iteraciones.

## Verificacion

Despues de cada cambio de codigo o documentacion, ejecutar `make check` para asegurar que no se introdujeron errores de linting ni tipado. Si no se puede ejecutar, reportar el motivo.

Comandos utiles existentes:

```sh
make cli
make api
make web
make web-build
make test
make check
```

Antes de dar por terminada una implementacion, correr las verificaciones relevantes y reportar si alguna no pudo ejecutarse.
