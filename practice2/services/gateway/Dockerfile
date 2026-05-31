FROM python:3.12-slim

WORKDIR /app

COPY services/gateway/requirements.txt ./services/gateway/requirements.txt
COPY requirements-test.txt ./requirements-test.txt
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 \
    -r services/gateway/requirements.txt \
    -r requirements-test.txt

COPY shared ./shared
COPY services/gateway ./services/gateway
COPY services/worker ./services/worker

ENV PYTHONPATH=/app:/app/services
EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
