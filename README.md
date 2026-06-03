# IT Patagonia x Luka Cerrutti - GenAI task

<p align="center">
  <img src="assets/it-patagonia-logo.png" alt="IT Patagonia" height="72" align="middle" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/lc-favicon.ico" alt="Luka Cerrutti" height="72" align="middle" />
</p>

Este proyecto implementa un orquestador agéntico para un **Ingeniero DevOps Virtual**. Recibe pedidos en lenguaje natural, interpreta la intención, planifica pasos seguros, ejecuta acciones simuladas con tools mockeadas y devuelve una traza auditable con estado final, TODOs, errores y recomendación.

> [!IMPORTANT]
> **Recorte de scope:**
> Como `definicion.pdf` dejaba abierta la elección de dominio y no especificaba integraciones concretas, el alcance se acotó a un caso DevOps/cloud. El objetivo no es construir un chatbot genérico ni provisionar infraestructura real, sino demostrar planificación, ejecución, retries, trazabilidad y comunicación sobre un dominio técnico claro.

## Arquitectura agéntica

El flujo está compuesto por tres agentes principales: `plannerAgent`, `executorAgent` y `summaryAgent`. LangGraph coordina el ciclo de planificar, ejecutar, observar y resumir, cortando antes de ejecutar cuando faltan datos o cuando el pedido no es válido.

```mermaid
flowchart LR
    START([__start__]) --> planner[planner]
    planner --> route{plan ejecutable?}
    route -->|sí| executor[executor]
    route -->|no| summary[summary]
    executor --> summary
    summary --> END([__end__])
```

- **planner:** interpreta el pedido, valida si hay información suficiente y produce TODOs ejecutables.
- **route_after_planner:** decide si el plan puede pasar a ejecución o debe ir directo al resumen.
- **executor:** ejecuta los TODOs en orden usando exclusivamente tools disponibles y reporta progreso incremental.
- **summary:** sintetiza el resultado final con estado, issues, TODOs, recomendación y traza.

> [!NOTE]
> **Las tools son mockeadas:**
> El proyecto registra 25 tools DevOps simuladas, incluyendo creación de buckets, bases de datos, VPN, firewall, IAM, backups, health checks, Kubernetes y Terraform. Todas devuelven respuestas locales en TOON, pueden modelar errores recuperables o definitivos, y el executor debe decidir retries o corte de ejecución según el resultado.

### Arquitectura de código

- [`app/agents/planner.py`](app/agents/planner.py): define el prompt, schema y ejecución del agente planificador.
- [`app/agents/executor.py`](app/agents/executor.py): define el agente ejecutor, bindea tools y expone updates de TODOs en vivo.
- [`app/agents/summary.py`](app/agents/summary.py): genera el resumen final sin inventar acciones ni resultados.
- [`app/graph.py`](app/graph.py): contiene el estado tipado, nodos LangGraph, routing, salida JSON y streaming SSE.
- [`app/main.py`](app/main.py): adaptador FastAPI con endpoints `POST /json`, `POST /sse` y documentación en `/docs`.
- [`app/settings.py`](app/settings.py): carga configuración desde entorno y [`.env.example`](.env.example), incluyendo Novita, CORS y modo de runtime.
- [`cli.py`](cli.py): adaptador Typer que ejecuta el mismo grafo y devuelve el mismo contrato JSON.
- [`app/tools/`](app/tools/): catálogo de tools DevOps mockeadas, sin llamadas a clouds reales.
- [`web/`](web/): interfaz estática Astro para probar el stream SSE y visualizar mensajes, TODOs y actividad.
- [`assets/`](assets/): logos e íconos usados por el README y la web.

#### Tooling en uso

El backend usa el ecosistema de LangChain para modelar agentes y tools, LangGraph para orquestar el flujo con estado explícito y LangSmith para trazabilidad cuando se configuran las variables de tracing. Novita AI se usa mediante una API compatible con OpenAI: `minimax/minimax-m3` corre en planner y summary por su foco en interpretación/síntesis, mientras que `zai-org/glm-5.1` corre en executor por su rol de selección de tools y seguimiento de pasos.

##### Qué mejoraría con más tiempo

Las integraciones externas hoy son mocks locales, útiles para demostrar el flujo, pero no para operar infraestructura real. También agregaría fallback de provider/modelo LLM, persistencia backend del historial y endurecimiento del contrato API para que la conversación no dependa principalmente del estado mantenido por el frontend.

## Cómo ejecutar

> [!TIP]
> **Web deployada:**
> La interfaz web está disponible en [patagonia.luka.software](https://patagonia.luka.software) y la documentación interactiva de la API en [api.patagonia.luka.software/docs](https://api.patagonia.luka.software/docs). Es la forma recomendada de probar el proyecto sin compartir API keys ni configurar entorno local. La API expone `POST /json` para obtener el reporte final y `POST /sse` para consumir eventos en tiempo real.

**Nota general:** Novita está un poco inestable y a veces da error al usar structured outputs con 120b. En caso de encontrar este error, por favor reintentar. Por supuesto, si lleváramos estos agentes a producción, usaríamos un proveedor más confiable.

Para ejecutar localmente se puede usar la CLI, la API FastAPI o la API junto con la web Astro. En todos los casos hace falta una API key de Novita y conviene revisar el [`makefile`](makefile) para ver los comandos disponibles.

1. Instalar dependencias de sistema: `uv` para Python. Si se va a usar la web, instalar también `bun`.
2. Instalar dependencias del proyecto con `make install`.
3. Crear `.env` desde [`.env.example`](.env.example) y completar al menos `NOVITA_API_KEY`. Opcionalmente completar `LANGSMITH_API_KEY` si se quiere tracing en LangSmith.

Para usar la CLI:

1. Ejecutar `make cli PROMPT="Crear un bucket S3 privado para staging"`.

Para usar solo la API:

1. Levantar la API con `make api`.
2. Abrir la documentación local en [localhost:8000/docs](http://localhost:8000/docs).
3. Probar `POST /json` para respuesta final o `POST /sse` para stream de eventos.

Para usar API + web local:

1. Levantar la API con `make api`.
2. En otra terminal, levantar la web con `make web`.
3. Abrir la URL local que imprime Astro y probar el flujo desde la interfaz.

Para verificar el proyecto:

1. Ejecutar `make check`.
