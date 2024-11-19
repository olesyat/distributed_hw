# Dockerfile for the master server
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server_master.py ./
COPY utils.py ./


CMD ["python", "server_master.py"]
