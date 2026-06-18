#!/bin/bash

# CampoEnOrden - Iniciar backend y frontend (local) o deploy a Vercel
# Uso:
#   ./start.sh              → inicia servidores locales
#   ./start.sh --deploy     → deploy a Vercel (production)
#   ./start.sh --dni <ID> <DNI>  → asigna DNI a usuario en prod

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend/campoenorden_backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend/campoenorden_frontend"
VENV_DIR="$SCRIPT_DIR/backend/venv"
REQS_BACKEND="$BACKEND_DIR/requirements.txt"
REQS_ROOT="$SCRIPT_DIR/requirements.txt"

# ── Helpers ──────────────────────────────────────────────────────────────────

sync_requirements() {
    echo "▶ Sincronizando requirements.txt raíz con backend..."
    if [ -f "$REQS_BACKEND" ]; then
        cp "$REQS_BACKEND" "$REQS_ROOT"
        echo "  ✓ $REQS_ROOT actualizado"
    fi
}

whatsapp_check() {
    missing=()
    [ -z "${WHATSAPP_ACCESS_TOKEN:-}" ] && missing+=("WHATSAPP_ACCESS_TOKEN")
    [ -z "${WHATSAPP_PHONE_NUMBER_ID:-}" ] && missing+=("WHATSAPP_PHONE_NUMBER_ID")

    if [ ${#missing[@]} -gt 0 ]; then
        echo "⚠  Variables de WhatsApp faltantes: ${missing[*]}"
        echo "   El chatbot no podrá responder mensajes."
        echo "   Configuralas en Vercel: vercel env add <NOMBRE> production"
    else
        echo "  ✓ Variables de WhatsApp OK"
    fi
}

# ── Deploy a Vercel ──────────────────────────────────────────────────────────

deploy_to_vercel() {
    echo ""
    echo "══════════════════════════════════════"
    echo "  Deploy a Vercel (production)"
    echo "══════════════════════════════════════"
    sync_requirements
    echo ""
    vercel deploy --prod
    echo ""
    echo "✓ Deploy completado."
    echo "  URL: https://campoenorden-api.vercel.app"
}

# ── Asignar DNI ──────────────────────────────────────────────────────────────

assign_dni() {
    local user_id="$1"
    local dni_value="$2"
    if [ -z "$user_id" ] || [ -z "$dni_value" ]; then
        echo "Uso: $0 --dni <USER_ID> <DNI>"
        echo "Ej:  $0 --dni 1 19372727"
        exit 1
    fi
    echo "▶ Asignando DNI=$dni_value al usuario ID=$user_id en producción..."
    source "$SCRIPT_DIR/.env.prod" 2>/dev/null || true
    python3 -c "
import os, psycopg2, sys
conn = psycopg2.connect(
    dbname=os.environ.get('PGDATABASE',''),
    user=os.environ.get('PGUSER',''),
    password=os.environ.get('PGPASSWORD',''),
    host=os.environ.get('PGHOST',''),
    port=os.environ.get('PGPORT','5432')
)
cur = conn.cursor()
cur.execute(\"UPDATE users_user SET dni=%s WHERE id=%s\", (sys.argv[2], sys.argv[1]))
print(f'Filas actualizadas: {cur.rowcount}')
conn.commit()
cur.close()
conn.close()
" "$user_id" "$dni_value"
    echo "✓ DNI asignado"
}

# ── Main ─────────────────────────────────────────────────────────────────────

MODE="${1:-local}"

case "$MODE" in
    --deploy|-d)
        deploy_to_vercel
        exit 0
        ;;
    --dni)
        shift
        assign_dni "$@"
        exit 0
        ;;
esac

# ── Local development ────────────────────────────────────────────────────────

cleanup() {
    echo ""
    echo "Deteniendo servidores..."
    [ ! -z "${BACKEND_PID:-}" ] && kill $BACKEND_PID 2>/dev/null
    [ ! -z "${FRONTEND_PID:-}" ] && kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

get_local_ip() {
    LOCAL_IP=$(python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('10.254.254.254', 1))
    print(s.getsockname()[0])
except:
    print('localhost')
finally:
    s.close()
" 2>/dev/null)
    if [ -z "$LOCAL_IP" ] || [ "$LOCAL_IP" = "localhost" ]; then
        LOCAL_IP=$(hostname -i 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^127' | head -1)
    fi
    [ -z "$LOCAL_IP" ] && LOCAL_IP="localhost"
    echo "$LOCAL_IP"
}

LOCAL_IP=$(get_local_ip)

echo ""
echo "══════════════════════════════════════"
echo "  CampoEnOrden - Inicio local"
echo "══════════════════════════════════════"
echo ""

# Sync requirements
sync_requirements

# WhatsApp check
whatsapp_check

# Matar procesos anteriores en los puertos
fuser -k 8000/tcp 2>/dev/null
fuser -k 8100/tcp 2>/dev/null
sleep 1

# Eliminar venv roto de Windows si existe
if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    WIN_CHECK=$(head -1 "$BACKEND_DIR/venv/bin/activate" | grep -i "windows\|cygwin" 2>/dev/null || echo "")
    if [ ! -z "$WIN_CHECK" ]; then
        echo "Eliminando venv obsoleto de Windows..."
        rm -rf "$BACKEND_DIR/venv"
    fi
fi

# ---------- BACKEND ----------
cd "$BACKEND_DIR" || exit 1

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if ! python -c "import django, requests, anthropic, rest_framework, corsheaders" 2>/dev/null; then
    echo "Instalando dependencias de Python..."
    pip install -r "$REQS_BACKEND"
fi

python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
sleep 2

# ---------- FRONTEND ----------
cd "$FRONTEND_DIR" || exit 1

[ ! -d "node_modules" ] && npm install

export PATH="/usr/local/bin:/usr/bin:$HOME/.npm/bin:$HOME/node/bin:$HOME/node/lib/node_modules/@ionic/cli/bin:$PATH"
[ -f "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

IONIC_CMD=""
if command -v ionic &> /dev/null; then
    IONIC_CMD="ionic"
elif [ -f "$HOME/node/bin/ionic" ]; then
    IONIC_CMD="$HOME/node/bin/ionic"
elif [ -f "$HOME/node/lib/node_modules/@ionic/cli/bin/ionic" ]; then
    IONIC_CMD="$HOME/node/lib/node_modules/@ionic/cli/bin/ionic"
elif command -v npx &> /dev/null; then
    IONIC_CMD="npx ionic"
fi

if [ -z "$IONIC_CMD" ]; then
    echo "Ionic CLI no encontrado. Intentando instalar..."
    npm install -g @ionic/cli
    IONIC_CMD="ionic"
fi

$IONIC_CMD serve --host 0.0.0.0 --port 8100 &
FRONTEND_PID=$!
sleep 2

echo ""
echo "Servidores iniciados:"
echo "  - Backend:  http://$LOCAL_IP:8000"
echo "  - Frontend: http://$LOCAL_IP:8100"
echo ""
echo "Para acceder desde otros dispositivos en la red usa: http://$LOCAL_IP:8100"
echo ""
echo "Comandos útiles:"
echo "  ./start.sh --deploy       → deploy a Vercel"
echo "  ./start.sh --dni <ID> <V> → asignar DNI en producción"
echo ""
echo "Presiona Ctrl+C para detener ambos servidores"

wait $BACKEND_PID $FRONTEND_PID
