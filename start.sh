#!/bin/bash

# CampoEnOrden - Iniciar backend y frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo "Deteniendo servidores..."
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    exit
}

trap cleanup INT TERM

echo "Iniciando backend Django..."
cd "$SCRIPT_DIR/backend/campoenorden_backend"
source venv/Scripts/activate
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

sleep 3

echo "Iniciando frontend Ionic..."
cd "$SCRIPT_DIR/frontend/campoenorden_frontend"
npx ionic serve --host 0.0.0.0 --port 8100
