#!/usr/bin/env bash
set -uo pipefail

BASE=/home/francisco/campoenorden
LOG="$BASE/tunnel.log"
URLFILE="$BASE/tunnel_url"
ENVFILE="$BASE/backend/campoenorden_backend/.env"
SERVICE=campoenorden

: > "$LOG"
/usr/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8000 > "$LOG" 2>&1 &
CF_PID=$!

URL=""
for _ in $(seq 1 120); do
    URL=$(grep -oE 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1 || true)
    [ -n "$URL" ] && break
    sleep 1
done

if [ -z "$URL" ]; then
    echo "No se obtuvo URL trycloudflare" >&2
    exit 1
fi

echo "$URL" > "$URLFILE"

HOST=$(echo "$URL" | sed 's|https://||; s|/.*||')

if grep -q '^ALLOWED_HOSTS=' "$ENVFILE"; then
    if ! grep -q "$HOST" "$ENVFILE"; then
        sed -i "s|^ALLOWED_HOSTS=.*|&,$HOST|" "$ENVFILE"
    fi
else
    echo "ALLOWED_HOSTS=$HOST,149.50.130.161,localhost,127.0.0.1" >> "$ENVFILE"
fi

# El backend corre en Docker desde 05/09/2026: reiniciar el contenedor para que
# tome el nuevo ALLOWED_HOSTS. Fallback a systemd si no esta dockerizado.
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'campoenorden-backend'; then
    cd /opt/stacks/campoenorden && docker compose restart backend >/dev/null 2>&1 || true
else
    systemctl restart "$SERVICE"
fi

wait "$CF_PID"