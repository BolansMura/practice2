#!/usr/bin/env bash
# Установка Prometheus + Grafana (kube-prometheus-stack) в Minikube
set -euo pipefail

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --wait --timeout 10m

echo "Apply ServiceMonitors for practice3 app:"
kubectl apply -f "$(dirname "$0")/servicemonitor-gateway.yaml"
kubectl apply -f "$(dirname "$0")/servicemonitor-worker.yaml"

echo ""
echo "Grafana:"
echo "  kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
echo "  Login: admin / prom-operator (or: kubectl get secret -n monitoring monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"
echo ""
echo "Prometheus:"
echo "  kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090"
