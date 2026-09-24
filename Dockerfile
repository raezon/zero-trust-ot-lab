# Image "tout-en-un" pour un DEPLOIEMENT GRATUIT sur un seul conteneur
# (Hugging Face Spaces, Render, Fly.io, Google Cloud Run...).
#
# Le lab pedagogique LOCAL, lui, utilise docker-compose.yml (4 reseaux Docker
# segmentes) et n'est PAS affecte par ce fichier. Ici, on regroupe les 3
# services : le navigateur ne parle qu'a la passerelle, qui appelle PLC/SCADA
# en interne (127.0.0.1) -> ces derniers ne sont jamais exposes publiquement.
FROM python:3.11-slim

WORKDIR /app

COPY services/plc     /app/plc
COPY services/scada   /app/scada
COPY services/gateway /app/gateway

RUN pip install --no-cache-dir \
    -r /app/gateway/requirements.txt \
    -r /app/plc/requirements.txt \
    -r /app/scada/requirements.txt

COPY deploy/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 7860 = port par defaut attendu par Hugging Face Spaces.
# Render / Cloud Run / Fly injectent la variable PORT, respectee par start.sh.
ENV PORT=7860 \
    PLC_URL=http://127.0.0.1:8001 \
    SCADA_URL=http://127.0.0.1:8002 \
    LAB_MODE=zero-trust

EXPOSE 7860
CMD ["/app/start.sh"]
