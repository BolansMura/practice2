FROM python:3.12-slim

WORKDIR /app

COPY services/worker/requirements.txt ./services/worker/requirements.txt
RUN pip install --no-cache-dir -r services/worker/requirements.txt

COPY shared ./shared
COPY services/worker ./services/worker

ENV PYTHONPATH=/app:/app/services
EXPOSE 9090

CMD ["python", "-m", "worker.main"]
