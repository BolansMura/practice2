# Без pip: pytest уже установлен в образе gateway (см. services/gateway/Dockerfile)
ARG GATEWAY_IMAGE=practice2-gateway:latest
FROM ${GATEWAY_IMAGE}

WORKDIR /app

COPY shared ./shared
COPY services ./services
COPY tests ./tests
COPY pytest.ini ./

ENV PYTHONPATH=/app:/app/services
CMD ["pytest", "-v"]
