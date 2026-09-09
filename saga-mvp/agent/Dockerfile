FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Port is read at runtime so the same image serves both agents on their
# own registered ports (AGENT_PORT is set per-service in docker-compose.yml).
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${AGENT_PORT:-9000} \
    --ssl-keyfile /certs/agent.key --ssl-certfile /certs/agent.crt"
