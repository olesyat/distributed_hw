## Dockerfile for the replicated server
#FROM python:3.11-slim
#
#WORKDIR /app
#
#COPY ./replica_1/requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt
#
#COPY ./replica_1/app.py ./
#
#CMD ["python", "app.py"]

# Dockerfile for the replicated server
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
