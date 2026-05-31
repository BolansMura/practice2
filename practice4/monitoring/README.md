# Конфигурация мониторинга

| Файл | Описание |
|------|----------|
| `helm-install.sh` | Установка kube-prometheus-stack + apply ServiceMonitor |
| `servicemonitor-gateway.yaml` | Сбор `/metrics` с Gateway :8000 |
| `servicemonitor-worker.yaml` | Сбор `/metrics` с Worker :9090 |
| `grafana-dashboard-idempotency.json` | Дашборд для импорта в Grafana |
