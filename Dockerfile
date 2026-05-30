FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app

COPY pyproject.toml uv.lock* ./
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH" ENV=production

EXPOSE 8080
CMD ["fastapi", "run", "app/main.py", "--port", "8080"]
