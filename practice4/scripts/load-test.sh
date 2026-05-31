#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-http://myapp.local}"
COUNT="${COUNT:-150}"

echo "Load test: ${COUNT} requests -> ${HOST}/execute"

ok=0
fail=0
for i in $(seq 1 "$COUNT"); do
  key=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${HOST}/execute" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: ${key}" \
    -d "{\"action\":\"process\",\"data\":{\"n\":${i}}}" || echo "000")
  if [[ "$code" == "202" || "$code" == "200" ]]; then
    ok=$((ok + 1))
  else
    fail=$((fail + 1))
    echo "fail #${i} http=${code}"
  fi
  if (( i % 25 == 0 )); then
    echo "progress ${i}/${COUNT} ok=${ok} fail=${fail}"
  fi
done

echo "Done: ok=${ok} fail=${fail}"
