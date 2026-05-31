FROM python:3.12-slim

WORKDIR /app

COPY services/gateway/requirements.txt ./services/gateway/requirements.txt
RUN pip install --no-cache-dir -r services/gateway/requirements.txt

COPY shared ./shared
COPY services/gateway ./services/gateway

ENV PYTHONPATH=/app:/app/services
EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
