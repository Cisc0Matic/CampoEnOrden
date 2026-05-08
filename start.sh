#!/bin/bash

# CampoEnOrden - Iniciar backend y frontend

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend/campoenorden_backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend/campoenorden_frontend"

cleanup() {
    echo ""
    echo "Deteniendo servidores..."
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Obtener IP local de forma portable
get_local_ip() {
    # Intentar con hostname -i (minúscula)
    LOCAL_IP=$(hostname -i 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^127' | head -1)
    
    # Si no funciona, intentar leyendo /etc/hosts
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP=$(grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' /etc/hosts | grep -v '127.0.0.1' | head -1 | awk '{print $1}')
    fi
    
    # Si aún no, usar la primera IP que no sea loopback
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP=$(ip addr 2>/dev/null | grep -oE 'inet [0-9.]+' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
    fi
    
    # Último recurso
    [ -z "$LOCAL_IP" ] && LOCAL_IP="localhost"
    echo "$LOCAL_IP"
}

LOCAL_IP=$(get_local_ip)

echo "Iniciando CampoEnOrden..."

# Matar procesos anteriores en los puertos
fuser -k 8000/tcp 2>/dev/null
fuser -k 8100/tcp 2>/dev/null
sleep 1

# ---------- BACKEND ----------
cd "$BACKEND_DIR" || exit 1

# Recrear venv si no funciona
if [ ! -f "venv/bin/activate" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependencias si hace falta
if ! python -c "import django" 2>/dev/null; then
    echo "Instalando dependencias de Python..."
    pip install -r requirements.txt
fi

python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

sleep 2

# ---------- FRONTEND ----------
cd "$FRONTEND_DIR" || exit 1

# Instalar node_modules si hace falta
[ ! -d "node_modules" ] && npm install

# Configurar PATH para node/npm  
export PATH="/usr/local/bin:/usr/bin:$HOME/.npm/bin:$HOME/node/bin:$PATH"
[ -f "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

# Buscar ionic
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
echo "Presiona Ctrl+C para detener ambos servidores"

wait $BACKEND_PID $FRONTEND_PID
