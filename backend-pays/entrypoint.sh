#!/bin/sh
# Démarrage du backend pays : on applique d'abord les migrations Alembic
# (autorité du schéma), puis on lance l'API. Si Alembic échoue, le seed du
# lifespan recrée le schéma via create_all (filet de sécurité), donc l'app
# démarre dans tous les cas.
set -e

echo "[entrypoint] Application des migrations Alembic..."
alembic upgrade head || echo "[entrypoint] WARN: migrations KO — repli create_all au démarrage"

echo "[entrypoint] Démarrage de l'API (pays=${COUNTRY:-BR})..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
