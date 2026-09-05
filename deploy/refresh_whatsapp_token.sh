#!/usr/bin/env bash
# Check semanal del token de WhatsApp — NO destructivo.
#
# Antes este script hacía `fb_exchange_token` sobre el token system-user (que es
# PERMANENTE, expires_at=0) y podía reemplazarlo por uno inválido para WhatsApp.
# Ahora solo valida el token contra Graph y loguea el resultado. Nunca escribe .env.
#
# Requiere LC_ALL=C.UTF-8 (Django lo exige al arrancar).
set -euo pipefail

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

PROJECT_DIR="${PROJECT_DIR:-/home/francisco/campoenorden}"
VENV_DIR="$PROJECT_DIR/backend/campoenorden_backend/venv"
MANAGE_DIR="$PROJECT_DIR/backend/campoenorden_backend"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/whatsapp_token_check.log"
MAX_FAILURES_FILE="$LOG_DIR/.whatsapp_token_failures"

mkdir -p "$LOG_DIR"

check_token() {
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'campoenorden-backend'; then
        docker exec campoenorden-backend python manage.py check_whatsapp_token 2>&1
    else
        cd "$MANAGE_DIR"
        "$VENV_DIR/bin/python" manage.py check_whatsapp_token 2>&1
    fi
}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] check_whatsapp_token start" >> "$LOG_FILE"

OUTPUT="$(check_token 2>&1)" || true

if echo "$OUTPUT" | grep -q "Token OK"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] OK: $OUTPUT" >> "$LOG_FILE"
    rm -f "$MAX_FAILURES_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FALLO: $OUTPUT" >> "$LOG_FILE"
    # Acumular fallos consecutivos: si son >=3, el token esta roto y hay que
    # regenerarlo en el panel de Meta, no automaticamente aqui.
    FAILURES=$(($(cat "$MAX_FAILURES_FILE" 2>/dev/null || echo 0) + 1))
    echo "$FAILURES" > "$MAX_FAILURES_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] check_whatsapp_token end" >> "$LOG_FILE"
exit 0