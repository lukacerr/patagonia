# IT Patagonia x Luka Cerrutti - GenAI task

// Poner aca los logos de /assets, uno al lado del otro horizontalmente

// aca dar un muy breve resumen del agente y el proyecto

> [!IMPORTANT] Recorte de scope
> // Explicar muy brevemente que como la definicion.pdf no era suficientemente especifica, se decidio cortar a un dominio especifico (devops agent)

## Arquitectura agéntica

// mini parrafo explicar que consta con 3 agentes, planner executor y summary

// realizar aquí un diagrama mmd del agente (similar al que exportaria langgraph con su generate mmd)

// bullet list que tiene *Titulo de nodo:* Breve descripcion de lo que pasa en ese nodo

> [!NOTE] Las tools son mockeadas
> // Aclarar la existencia de +20 tools pero que son todas mockeadas, con cierta chance de error y retry y blah blah blah

### Arquitectura de código

// Bullet list explicando cada archivo y que tiene/hace muy brevemente. No entrar en detalles en la /web nni en las /tools

#### Tooling en uso

// Write-up peque;o sobre que se esta usando el ecosistema de langchain, langgraph, langsmith para trazabilidad, con novita, gpt oss y glm, dar contexto en donde y porque esta seleccion.

##### Que mejoraría con más tiempo

// mini writeup explicando que las tools son todas mockeadas, no hay fallback de provider de LLM y el historial actualmente se maneja via front-end

## Como ejecutar

> [!TIP] Web deployada
> // Explicar que está la interfaz web deployada en https://patagonia.luka.software y docs de la API en https://api.patagonia.luka.software/docs, pueden usar esto para probar asi no tenemos que estar compartiendo api keys, thus es altamente recomendable que lo prueben desde acá. explicar que está el endpoint de JSON o el SSE del lado de la API.

// en caso de querer proceder con ejecucion, explicar que está o la API o la CLI, que requiere api key de novita, que se refieran al makefile para instalar y que creen el .env con las variables correspondientes del example, hacer una numbered list paso a paso para que puedan hacer esto si lo desean
