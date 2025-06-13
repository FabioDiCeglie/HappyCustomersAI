FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN uv pip install --no-cache -r pyproject.toml

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./backend/app ./app
# COPY ./backend/.env .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--reload"]