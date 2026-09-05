# Deploy Producción Provisorio — DonWeb (149.50.130.161) + Netlify

Arquitectura actual (5 sep 2026): **frontend SPA en Netlify** + **backend API en el
VPS de DonWeb**, con HTTPS público del API provisorio vía **quick tunnel de
cloudflared (trycloudflare)** para que Meta acepte el webhook de WhatsApp.
Reemplaza el stack anterior (Netlify + Vercel + Neon) y el experimento Green API.

## Estado actual (5 sep 2026)

| Componente | URL / Detalle |
|------------|---------------|
| Frontend (SPA) | https://campoenorden.netlify.app |
| Backend API (provisorio) | https://member-dreams-matched-bill.trycloudflare.com/api ⚠️ cambia en cada reinicio del túnel |
| Backend API (interno) | http://149.50.130.161/api |
| Admin Django | https://member-dreams-matched-bill.trycloudflare.com/admin / http://149.50.130.161/admin |
| Webhook WhatsApp | https://member-dreams-matched-bill.trycloudflare.com/api/chatbot/webhook/ |
| Base de datos | PostgreSQL 15 local en el server (db `campoenorden`) |
| Landing (marketing) | no servida en el SPA (fue reemplazada por la app en la raíz) |

## Server

- IP: `149.50.130.161` · SSH: `ssh -p 5262 francisco@149.50.130.161`
- OS: Debian 12 (bookworm) · 4 vCPU Intel Broadwell · 7.8 GiB RAM · 13G disco
- En el mismo server ya corren: **Odoo** (8069/8070/8072 + Cloudflare tunnel) y
  **nginx**. **No tocar esos servicios.**
- Runtimes instalados: Python 3.12.14 (vía `uv`), Node 20.20.2 (NodeSource),
  PostgreSQL 15.19 (paquete del sistema), `postgresql-client-17` (pgdg, para dumps).

## Arquitectura en el server

```
Internet ──► nginx :80 (server_name 149.50.130.161)
              ├── /              → SPA Angular (www/)  [try_files → /index.html]
              ├── /api/          → proxy → gunicorn 127.0.0.1:8000
              ├── /admin/        → proxy → gunicorn 127.0.0.1:8000
              ├── /static/       → staticfiles/ (collectstatic, nginx directo)
              └── /media/        → media/ (uploads, nginx directo)
```

- gunicorn corre como servicio systemd `campoenorden` (WSGI de Django).
- Django levanta con settings de **producción** vía `DJANGO_SETTINGS_MODULE` en el unit.

## Código en el server

- Ruta: `/home/francisco/campoenorden/`
  - `backend/campoenorden_backend/` → Django + venv (`.venv`) + `.env`
  - `frontend/campoenorden_frontend/` → fuente Angular; build en `www/`
  - `scripts/refresh_whatsapp_token.sh` → cron de token
  - `logs/token_refresh.log` → log del cron
  - `campoenorden_backup/` → dumps SQL de la base (Neon → local)
- Origen: rsync desde la máquina local (`rsync -az --delete … francisco@…:campoenorden/`).
  Método de actualización: volver a rsync + rebuild del frontend.

## Archivos de configuración claves

### 1. `.env` del backend (`~/campoenorden/backend/campoenorden_backend/.env`)

```ini
DJANGO_SECRET_KEY=<secreto generado en el server>
DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production
DJANGO_HTTPS=0
ALLOWED_HOSTS=149.50.130.161,localhost,127.0.0.1,member-dreams-matched-bill.trycloudflare.com
CORS_ALLOWED_ORIGINS=http://149.50.130.161,http://localhost:8100,https://campoenorden.netlify.app
FRONTEND_URL=https://campoenorden.netlify.app
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=campoenorden
PGUSER=campoenorden
PGPASSWORD=ceo_prod_local_2026
EMAIL_HOST_USER=campoenorden2026@gmail.com
EMAIL_HOST_PASSWORD=<gmail smtp app password>
WHATSAPP_ACCESS_TOKEN=<system user token, permanente>
WHATSAPP_PHONE_NUMBER_ID=1170424916153681
WHATSAPP_WEBHOOK_VERIFY_TOKEN=campoenorden_webhook_2026
WHATSAPP_APP_SECRET=<app secret>
FACEBOOK_APP_ID=1523301969430270
FACEBOOK_APP_SECRET=<app secret>
ANTHROPIC_API_KEY=
RESEND_API_KEY=
```

> `DJANGO_HTTPS=0` deja `SECURE_SSL_REDIRECT` apagado. Al pasar por el túnel de
> cloudflared se recibe `X-Forwarded-Proto: https`, así Django trata la request como
> segura (el header está configurado en `production.py`). El host del túnel se agrega
> automáticamente a `ALLOWED_HOSTS` por el script `tunnel_campoenorden.sh`.

### 2. Unit de systemd (`/etc/systemd/system/campoenorden.service`)

```ini
[Unit]
Description=CampoEnOrden Django backend (gunicorn)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=francisco
Group=francisco
WorkingDirectory=/home/francisco/campoenorden/backend/campoenorden_backend
Environment=DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production
ExecStart=/home/francisco/campoenorden/backend/campoenorden_backend/.venv/bin/gunicorn campoenorden_backend.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 90
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 3. nginx (`/etc/nginx/sites-available/campoenorden`, symlink en sites-enabled)

```nginx
server {
    listen 80;
    server_name 149.50.130.161 localhost;
    server_tokens off;

    root /home/francisco/campoenorden/frontend/campoenorden_frontend/www;
    index index.html;

    client_max_body_size 25M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ { proxy_pass http://127.0.0.1:8000; ... }

    location /static/ { alias /home/francisco/campoenorden/backend/campoenorden_backend/staticfiles/; }
    location /media/  { alias /home/francisco/campoenorden/backend/campoenorden_backend/media/; }

    location / { try_files $uri $uri/ /index.html; }
}
```

> `/home/francisco` está en `711` para que nginx (www-data) pueda atravesarlo.

### 4. Sudoers NOPASSWD (para el cron reinicie gunicorn)

`/etc/sudoers.d/campoenorden`:
```
francisco ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart campoenorden
```

### 5. Cron (refresh token WhatsApp, cada 50 días)

```
0 0 */50 * * /home/francisco/campoenorden/scripts/refresh_whatsapp_token.sh
```

### 6. Quick tunnel HTTPS para el API (webhook de Meta)

Servicio systemd `cloudflared-campoenorden` que levanta un **quick tunnel de
cloudflared** hacia `http://127.0.0.1:8000` (igual concepto que el de Odoo, sin
tocarlo). La URL es `https://<random>.trycloudflare.com` y **cambia en cada
reinicio** del servicio.

- Script: `/home/francisco/campoenorden/scripts/tunnel_campoenorden.sh`
- Unit: `/etc/systemd/system/cloudflared-campoenorden.service` (`Restart=always`)
- Log: `/home/francisco/campoenorden/tunnel.log` · URL actual: `/home/francisco/campoenorden/tunnel_url`
- Responsabilidades del script (idempotente):
  1. Lanza `cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8000` y
     captura la URL `https://…trycloudflare.com` del log.
  2. Agrega el host a `ALLOWED_HOSTS` del `.env` (si no está) y
     `systemctl restart campoenorden`.
- Operación: `sudo systemctl restart cloudflared-campoenorden`.

> ⚠️ Al reiniciar el túnel, **la URL cambia** y hay que hacer 3 cosas:
> 1. Re-registrar el webhook en Meta con la nueva `callback_url` (ver abajo).
> 2. Rebuild + redeploy del frontend (`environment.prod.ts` → `apiUrl` nuevo).
> 3. (Se mantiene igual: CORS/ALLOWED_HOSTS los resuelve el script).

## Base de datos local

- Cluster PostgreSQL 15 del sistema (`postgresql@15-main`), solo `127.0.0.1:5432`.
- Rol/db: `campoenorden` / `campoenorden` (UTF8, `TEMPLATE template0`, collate C).
- Los datos se migraron desde Neon.tech (PG 17.11) con:
  ```bash
  /usr/lib/postgresql/17/bin/pg_dump -h <neon-host> -U neondb_owner -d neondb \
      --no-owner --no-privileges -Fp -f ~/campoenorden_backup/neon_dump_YYYYMMDD.sql
  # quitar la línea "SET transaction_timeout = 0;" (GUC de PG17 inexistente en PG15)
  sed -i '/^SET transaction_timeout/d' ~/campoenorden_backup/neon_dump_*.sql
  PGPASSWORD=ceo_prod_local_2026 psql -h 127.0.0.1 -U campoenorden -d campoenorden -f <dump>
  ```
- Restaurados: 36 tablas, 4 usuarios, 5 grupos, 270 mensajes WhatsApp, sesiones, etc.
- Superuser admin: `admin` / `19LTBm1E5y2Xf36` (**cambiarlo**).

## Cómo se desplegó (paso a paso)

1. Instalación de runtime:
   - `uv` (astral) → `uv python install 3.12` (Python 3.12.14 en `~/.local/share/uv/…`)
   - NodeSource `setup_20.x` → Node 20.20.2
   - repo pgdg + `postgresql-client-17` (pg_dump 17)
2. Creación de rol/bd Postgres (con `template0`, collate C).
3. Dump + restore desde Neon (ver arriba).
4. rsync del código al server (excluyendo `node_modules`, `www`, `.venv`, `.git`, `.env*`, zips/pdfs).
5. Backend:
   ```bash
   cd ~/campoenorden/backend/campoenorden_backend
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -r requirements.txt
   uv pip install --python .venv/bin/python gunicorn
   # crear .env, luego:
   DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production .venv/bin/python manage.py migrate
   DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production .venv/bin/python manage.py collectstatic --noinput
   # crear superuser admin
   ```
6. Unit systemd + `systemctl enable --now campoenorden`.
7. Frontend (en la máquina local 🖥️ — ahora se hostea en **Netlify**):
   ```bash
   cd frontend/campoenorden_frontend
   npm ci --no-audit --no-fund
   # environment.prod.ts: apiUrl = 'https://<url-del-tunel>/api'
   npm run build -- --configuration=production              # → www/
   cd ..
   netlify deploy --prod --site 4e24c4e3-c6b2-41c0-9482-add1d7061eb0 --dir frontend/campoenorden_frontend/www
   #   → https://campoenorden.netlify.app  (token: netlify status → Personal access tokens)
   ```
   > El `netlify.toml` del repo define build (`npm install --include=dev && npm run build`,
   > Node 20, publish `www`) y el redirect SPA `/* → /index.html`.
8. nginx site `campoenorden` + `nginx -t` + reload.
9. Cron de token + sudoers NOPASSWD.
10. Quick tunnel: copiar `scripts/tunnel_campoenorden.sh` + unit `cloudflared-campoenorden`
    y `systemctl enable --now cloudflared-campoenorden`.

## Verificación

```bash
# desde cualquier máquina
curl -o /dev/null -w '%{http_code}\n' https://campoenorden.netlify.app/            # 200 (SPA)
curl -s https://member-dreams-matched-bill.trycloudflare.com/api/chatbot/health/   # JSON meta_token valid
curl -s "https://member-dreams-matched-bill.trycloudflare.com/api/chatbot/webhook/?hub.mode=subscribe&hub.verify_token=campoenorden_webhook_2026&hub.challenge=test123"  # test123
curl -o /dev/null -w '%{http_code}\n' http://149.50.130.161/admin/login/           # 200
curl -o /dev/null -w '%{http_code}\n' http://149.50.130.161/static/admin/css/base.css  # 200
# en el server
systemctl is-active campoenorden nginx postgresql odoo cloudflared-odoo-odoo cloudflared-campoenorden
```

> El health responde **503** con `token_error` hasta cargar `WHATSAPP_ACCESS_TOKEN`.

## Operación diaria

- **Reiniciar backend:** `sudo systemctl restart campoenorden`
- **Ver logs backend:** `sudo journalctl -u campoenorden -f`
- **Ver logs nginx:** `tail -f /var/log/nginx/error.log`
- **Backup BD:** `pg_dump` local (con `pg_dump` del sistema en PG15):
  ```bash
  PGPASSWORD=ceo_prod_local_2026 pg_dump -h 127.0.0.1 -U campoenorden -d campoenorden -Fc \
      -f ~/campoenorden_backup/local_$(date +%Y%m%d).dump
  ```
- **Actualizar app:** rsync del código → `collectstatic` → rebuild frontend → `sudo systemctl restart campoenorden`.

## WhatsApp por Meta Cloud API (webhook vía túnel)

El backend corre el provider **`meta`** (Cloud API oficial). El webhook se
registró a nivel app en Meta apuntando a la URL del túnel:

- Callback URL: `https://member-dreams-matched-bill.trycloudflare.com/api/chatbot/webhook/`
- Verify token: `campoenorden_webhook_2026`
- Suscripción: `POST /{app-id}/subscriptions` con `object=whatsapp_business_account`, fields `messages,message_template_status_update,account_update`.

Comandos útiles en el server:
```bash
cd ~/campoenorden/backend/campoenorden_backend
export LC_ALL=C.UTF-8
DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production .venv/bin/python manage.py check_whatsapp_token
curl -sk "https://$(cat ~/campoenorden/tunnel_url)/api/chatbot/health/"
```

**Verificar/re-registrar el webhook** (cuando cambie la URL del túnel):
```bash
APPTOKEN="$(curl -s "https://graph.facebook.com/v21.0/oauth/access_token?client_id=<FACEBOOK_APP_ID>&client_secret=<FACEBOOK_APP_SECRET>&grant_type=client_credentials" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')"
PROOF="$(APPTOKEN="$APPTOKEN" python3 -c 'import hmac,hashlib,os;print(hmac.new(os.environ["FACEBOOK_APP_SECRET"].encode(),os.environ["APPTOKEN"].encode(),hashlib.sha256).hexdigest())')"  # con las envs correspondientes
curl -s -X POST "https://graph.facebook.com/v21.0/<FACEBOOK_APP_ID>/subscriptions" \
  -d "object=whatsapp_business_account" \
  -d "callback_url=https://<nueva-url-tunel>/api/chatbot/webhook/" \
  -d "verify_token=campoenorden_webhook_2026" \
  -d "fields=messages,message_template_status_update,account_update" \
  -d "access_token=$APPTOKEN" -d "appsecret_proof=$PROOF"
```

**Cómo testear E2E:** mensajeá `HOLA` al `+1 555-656-7570` (Test Number):
1. `HOLA` → si el número no coincide con un usuario activo de la BD, el bot pide DNI;
   ingresá un DNI activo (ej: `19372727` = produser1, `43813147` = Francis).
2. Menú → `1. Labores` → `1. Pulverización` → campo → lote → producto
   (`Roundup - 3 L/ha - 15 L`) → `LISTO` → confirmar.
3. Verificar en BD: `SELECT * FROM chatbot_whatsappmessage ORDER BY id DESC LIMIT 10;`
   y en `core_labor`/`core_laborinsumo` la labor cargada.

## Pendientes / limitaciones conocidas

1. **Túnel provisorio**: la URL `trycloudflare` cambia en cada reinicio → hay que
   re-registrar el webhook en Meta y re-deployar el frontend. Producir está: comprar
   un dominio para el API, punto CNAME/directo al túnel con hostname propio (como
   Odoo: `odoo.unnuevosantigo.online`), setear `DJANGO_HTTPS=1` y actualizar
   `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/`FRONTEND_URL` de una sola vez.
2. **`ANTHROPIC_API_KEY` y `RESEND_API_KEY` vacías** → sin visión Claude y sin email
   real vía Resend (hay fallback Gmail SMTP ya funcionando).
3. Disco: ~8G libres. `node_modules` del build ocupa ~2G. Cuidar el espacio.
4. Landing de marketing de Django (raíz `''`) queda eclipsada por el SPA; si se
   necesita, servirla en `/landing` con un `location` extra.
5. Green API: **eliminado** (los `providers/`, `chatbot_poll_greenapi.py`, service
   `campoenorden-greenapi` y envs `CHAT_PROVIDER`/`GREEN_API_*` no existen más; el
   snapshot quedó en la rama git `greenapi-experiment`).

## Credenciales de referencia (provisorias)

| Recurso | Valor |
|---------|-------|
| SSH | `ssh -p 5262 francisco@149.50.130.161` (clave pública de `fran@zenbook`) |
| sudo (francisco) | password del usuario `francisco` |
| Postgres local | `campoenorden` / `ceo_prod_local_2026` (db `campoenorden`, host 127.0.0.1) |
| Admin Django | `admin` / `19LTBm1E5y2Xf36` (cambiar) |
| Netlify | site `campoenorden` → https://campoenorden.netlify.app (token PAT personal de `francis bar`/`agusbarriobarrio87@gmail.com`) |
| Meta / WhatsApp | ver `.env` del server (`campoenorden_backend/.env`): FACEBOOK_APP_ID `1523301969430270`, PHONE_NUMBER_ID `1170424916153681`, verificado `+1 555-656-7570`, token system user permanente (protegerlo; la app exige `appsecret_proof`) |
| Túnel API (provisorio) | `https://<random>.trycloudflare.com` → `/home/francisco/campoenorden/tunnel_url` |
| Base anterior (Neon) | host `ep-frosty-lab-aj904li8-pooler.c-3.us-east-2.aws.neon.tech`, user `neondb_owner` |

> ⚠️ Los archivos `.env*` locales NO se suben a git (`.gitignore`). El `.env` del
> server es la única copia de las credenciales de producción local.