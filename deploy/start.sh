#!/bin/sh
# Demarre les 3 services dans UN seul conteneur (deploiement gratuit).
# La passerelle est publique ; PLC et SCADA restent en interne (127.0.0.1),
# donc jamais joignables directement de l'exterieur (segmentation preservee).
set -e

: "${PORT:=7860}"
export PLC_URL="${PLC_URL:-http://127.0.0.1:8001}"
export SCADA_URL="${SCADA_URL:-http://127.0.0.1:8002}"
export LAB_MODE="${LAB_MODE:-zero-trust}"
export DATA_DIR="${DATA_DIR:-/app/gateway/data}"

# Ressources internes (non exposees)
( cd /app/plc   && uvicorn app:app --host 127.0.0.1 --port 8001 ) &
( cd /app/scada && uvicorn app:app --host 127.0.0.1 --port 8002 ) &

# Laisse les ressources demarrer
sleep 2

# Passerelle publique (seule exposee)
cd /app/gateway
exec uvicorn app:app --host 0.0.0.0 --port "$PORT"
