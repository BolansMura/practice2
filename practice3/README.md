# Practice 3 — Kubernetes (Minikube)

Деплой микросервисов из [practice2](../practice2/README.md) в Minikube.

## Микросервисы и образы

| Сервис | Deployment | Service | Образ |
|--------|------------|---------|--------|
| Redis | `redis` (1) | `redis` ClusterIP :6379 | `redis:7-alpine` |
| API Gateway | `gateway` (2) | `gateway` ClusterIP :8000 | `practice2-gateway:latest` |
| Worker | `worker` (1) | `worker` ClusterIP :9090 | `practice2-worker:latest` |

Ingress: `myapp.local` → Service `gateway:8000`

## Быстрый старт (WSL)

```bash
# 1. Кластер
minikube start --driver=docker
minikube addons enable ingress

# 2. Образы в Minikube
sed -i 's/\r$//' practice3/scripts/build-minikube-images.sh
bash practice3/scripts/build-minikube-images.sh

# 3. Деплой
kubectl apply -f practice3/k8s/

# 4. Туннель (отдельный терминал, sudo)
minikube tunnel

# 5. hosts (Windows: C:\Windows\System32\drivers\etc\hosts)
# 127.0.0.1 myapp.local
echo "127.0.0.1 myapp.local" | sudo tee -a /etc/hosts

# 6. Проверка
kubectl get pods,svc,ingress -n practice3
curl http://myapp.local/health
```

## Манифесты (`k8s/`)

- `namespace.yaml`, `configmap.yaml`, `secret.yaml`
- `pvc-redis.yaml`, `deployment-redis.yaml`, `service-redis.yaml`
- `deployment-gateway.yaml`, `service-gateway.yaml`
- `deployment-worker.yaml`, `service-worker.yaml`
- `ingress.yaml`

## Диагностика

```bash
kubectl get pods,deploy,svc,ingress -n practice3
kubectl logs -n practice3 deploy/gateway
kubectl logs -n practice3 deploy/worker
kubectl describe pod -n practice3 -l app=gateway
```

Отчёт: [PRACTICE3.md](PRACTICE3.md)
