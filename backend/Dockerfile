FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN uv pip install --no-cache .

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./app ./app
# Use this below just for local development
# COPY ./backend/.env .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT