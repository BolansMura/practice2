# Practice 4 — Мониторинг (Prometheus + Grafana)

## Быстрый старт

```bash
# 1. Minikube + приложение practice3 уже должны работать
minikube start --driver=docker

# 2. Helm (если нет)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 3. Стек мониторинга + ServiceMonitor
sed -i 's/\r$//' practice4/monitoring/helm-install.sh
bash practice4/monitoring/helm-install.sh

# 4. Пересобрать образы с бизнес-метриками
sed -i 's/\r$//' practice4/scripts/rebuild-app-images.sh
bash practice4/scripts/rebuild-app-images.sh

# 5. Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# http://localhost:3000  user: admin  pass: prom-operator (или см. secret)

# 6. Импорт дашборда: Dashboards → Import → practice4/monitoring/grafana-dashboard-idempotency.json

# 7. Нагрузка (minikube tunnel в другом терминале)
sed -i 's/\r$//' practice4/scripts/load-test.sh
bash practice4/scripts/load-test.sh
# или: sed -i 's/\r$//' practice4/scripts/load-test.sh && bash practice4/scripts/load-test.sh
```

Отчёт: [PRACTICE4.md](PRACTICE4.md)
