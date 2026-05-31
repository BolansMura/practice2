#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PRACTICE2="${ROOT}/practice2"

if ! command -v minikube >/dev/null 2>&1; then
  echo "minikube not found"
  exit 1
fi

echo "Using Minikube Docker daemon..."
eval "$(minikube docker-env)"

cd "${PRACTICE2}"
docker build -t practice2-gateway:latest -f services/gateway/Dockerfile .
docker build -t practice2-worker:latest -f services/worker/Dockerfile .

echo "Images ready in Minikube:"
docker images | grep -E "practice2-(gateway|worker)"
