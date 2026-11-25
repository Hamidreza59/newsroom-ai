FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services
RUN uv sync --frozen --no-dev --no-editable --package newsroom-mcp

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 newsroom \
    && mkdir -p /data/out /data/state && chown -R newsroom /data
COPY --from=build /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH OUT_DIR=/data/out DATA_DIR=/data/state MCP_HOST=0.0.0.0
USER newsroom
WORKDIR /home/newsroom
VOLUME /data
EXPOSE 8765
ENTRYPOINT ["newsroom-mcp"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8765"]
