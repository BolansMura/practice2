#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
eval "$(minikube docker-env)"
cd "${ROOT}/practice2"
docker build -t practice2-gateway:latest -f services/gateway/Dockerfile .
docker build -t practice2-worker:latest -f services/worker/Dockerfile .
kubectl rollout restart deployment/gateway deployment/worker -n practice3
kubectl rollout status deployment/gateway -n practice3
kubectl rollout status deployment/worker -n practice3
