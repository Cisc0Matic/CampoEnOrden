# CampoEnOrden — Guía de Deploy

## Stack

| Capa | Tecnología | Hosting |
|---|---|---|
| Frontend | Ionic 8 + Angular 20 | Netlify |
| Backend | Django 6 + DRF | Vercel (Python Serverless) |
| Base de datos | PostgreSQL | Neon.tech |
| Email | Resend API / Gmail SMTP | — |

---

## URLs activas

| Componente | URL |
|---|---|
| Frontend | https://starlit-puppy-3b26d1.netlify.app |
| Backend API | https://campoenorden-api.vercel.app |
| Base de datos | `ep-frosty-lab-aj904li8-pooler.c-3.us-east-2.aws.neon.tech` |

---

## 1. Deploy del Frontend (Netlify)

### Prerequisitos
- Token de acceso personal de Netlify (generar en https://app.netlify.com/user/applications#personal-access-tokens)

### Build
```bash
cd frontend/campoenorden_frontend
npm run build -- --configuration=production
```

El output queda en `frontend/campoenorden_frontend/www/`.

### Deploy
```bash
cd frontend/campoenorden_frontend
export NETLIFY_AUTH_TOKEN=nfp_dJpPEC9kz7XtGdHFQrrUEeLDWAaZgCX5ab9b
npx netlify-cli deploy --prod --no-build --dir=www
```

> **Importante**: Usar `--no-build` porque el build ya se hizo localmente. Sin esa flag Netlify intenta rebuildear y puede fallar por versión de Node local.

### Config
- `netlify.toml` en la raíz del proyecto
- Node version: `20`
- Build command: `npm install --include=dev && npm run build`
- Publish dir: `www`
- `_redirects`: `/* /index.html 200` (SPA routing)

---

## 2. Deploy del Backend (Vercel)

### Prerequisitos
- Vercel CLI instalado
- Proyecto ya linkeado (`.vercel/project.json` existe)

### Deploy
```bash
cd /home/fran/CampoEnOrden
vercel --prod
```

### Variables de entorno (producción)

Configuradas via `vercel env add <KEY> production` o desde el dashboard de Vercel:

| Variable | Valor |
|---|---|
| `ALLOWED_HOSTS` | `.vercel.app,localhost,127.0.0.1,campoenorden-api.vercel.app` |
| `CORS_ALLOWED_ORIGINS` | `https://starlit-puppy-3b26d1.netlify.app,http://localhost:8100` |
| `DJANGO_SECRET_KEY` | `django-insecure-prod-<random>` |
| `FRONTEND_URL` | `https://starlit-puppy-3b26d1.netlify.app` |
| `PGHOST` | `ep-frosty-lab-aj904li8-pooler.c-3.us-east-2.aws.neon.tech` |
| `PGUSER` | `neondb_owner` |
| `PGPASSWORD` | `npg_7wfyc6ugVYaR` |
| `PGDATABASE` | `neondb` |

### Entry point
- Archivo: `/api/index.py` (raíz del proyecto)
- Carga Django con `DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production`
- Agrega `backend/campoenorden_backend` al Python path

### Config
- `vercel.json` en la raíz con builder `@vercel/python`
- `requirements.txt` en la raíz (necesario para que `uv` lo detecte)

---

## 3. Base de datos (Neon.tech)

- Host: `ep-frosty-lab-aj904li8-pooler.c-3.us-east-2.aws.neon.tech`
- Database: `neondb`
- User: `neondb_owner`
- Password: `npg_7wfyc6ugVYaR`
- Cadena de conexión:
  ```
  postgresql://neondb_owner:npg_7wfyc6ugVYaR@ep-frosty-lab-aj904li8-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require
  ```
- Pooler: usar host con `-pooler` para serverless (Vercel)

---

## 4. Email

Configuración en `backend/campoenorden_backend/campoenorden_backend/settings/base.py`:

- **Resend API** (preferido): necesita `RESEND_API_KEY` en entorno
- **Gmail SMTP** (fallback):
  - User: `campoenorden2026@gmail.com`
  - Password: `rwsgicbnzzvnxvrw`
- **Console** (último recurso): imprime en stdout, no envía

---

## 5. Archivos críticos

### Frontend
| Archivo | Propósito |
|---|---|
| `frontend/campoenorden_frontend/src/environments/environment.prod.ts` | URL del backend API |
| `frontend/campoenorden_frontend/src/environments/environment.ts` | URL del backend (dev: `/api`) |
| `netlify.toml` | Config de build y deploy Netlify |

### Backend
| Archivo | Propósito |
|---|---|
| `api/index.py` | Entry point serverless de Vercel |
| `vercel.json` | Config de build y rutas Vercel |
| `requirements.txt` | Dependencias Python |
| `backend/campoenorden_backend/campoenorden_backend/settings/base.py` | Config compartida |
| `backend/campoenorden_backend/campoenorden_backend/settings/production.py` | Config producción |
| `backend/campoenorden_backend/campoenorden_backend/settings/development.py` | Config desarrollo |
| `backend/campoenorden_backend/.env` | Email credentials local |
| `backend/campoenorden_backend/.env.local` | Vars locales creadas por Vercel CLI |
| `.env.vercel` | Template de vars de entorno |

---

## 6. Desarrollo local

### Backend
```bash
cd backend/campoenorden_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd frontend/campoenorden_frontend
npm install
npx ionic serve --host 0.0.0.0 --port 8100
```

Dev proxy en `proxy.conf.json`: `/api` → `http://localhost:8000`

---

## 7. Troubleshooting

### Frontend: muchas requests al cambiar de tab
**Síntoma**: 8-16 llamadas a la misma API al navegar entre tabs.
**Causa**: Uso de `router.events` + `ngOnInit` en todas las pages.
**Solución**: Reemplazar por `ionViewWillEnter()` (hook de Ionic que se dispara naturalmente al entrar al tab). Ver páginas en `src/app/*/`.

### Frontend: console.logs en producción
**Síntoma**: Mensajes como "Interceptor: Token encontrado en Storage. Clonando headers..." en la consola del browser.
**Causa**: `auth/auth.interceptor.ts` tiene 8 statements de `console.log/warn`.
**Solución**: Eliminarlos (ya hecho).

### Backend: "No module named 'django'" en Vercel
**Causa**: `uv` (gestor de paquetes de Vercel) no encuentra `requirements.txt`.
**Solución**: Copiar `requirements.txt` a la raíz del proyecto (ya hecho).

### Backend: "settings.py" vs "settings/" conflict
**Síntoma**: Error de importación en Vercel o local.
**Causa**: Coexisten `settings.py` (archivo) y `settings/` (directorio) en el mismo paquete Python.
**Solución**: Eliminar `settings.py` (ya hecho). Solo debe existir el directorio `settings/` con `__init__.py`.

### Backend: FUNCTION_INVOCATION_FAILED
**Causa**: Falta de variables de entorno en Vercel.
**Solución**: Configurar todas las variables de producción via `vercel env add` o dashboard.

### Base de datos: SSL required
Neon requiere SSL. `production.py` usa `psycopg2-binary` que maneja SSL automáticamente con la cadena de conexión que incluye `sslmode=require`.

---

## 8. Tokens y credenciales sensibles

| Recurso | Dónde está | Nota |
|---|---|---|
| Netlify token | `nfp_dJpPEC9kz7XtGdHFQrrUEeLDWAaZgCX5ab9b` | Token personal del dueño del repo |
| Netlify site ID | `162346b0-dfbc-47ba-ba20-8d7bf664dfd7` | `starlit-puppy-3b26d1` |
| Vercel project ID | `prj_iYOcdl2ZAz2J7L30pE9odPWFVFsd` | `campoenorden-api` |
| Vercel org ID | `team_XKz4Ks7PaIPqckT8CRAtUS4m` | `agusbarriobarrio-4016s-projects` |
| Neon DB password | `npg_7wfyc6ugVYaR` | En `.env.local` y `.env.vercel` |
| Gmail SMTP password | `rwsgicbnzzvnxvrw` | En `backend/campoenorden_backend/.env` |
| Gmail user | `campoenorden2026@gmail.com` | En `.env` |

> **⚠️ Estos archivos `.env*` están en `.gitignore` y no se suben al repo. Si se pierden, hay que regenerarlos desde el dashboard de cada servicio.**

---

## 9. Quick Deploy (todo en uno)

```bash
# 1. Build frontend
cd frontend/campoenorden_frontend && npm run build -- --configuration=production

# 2. Deploy frontend a Netlify
export NETLIFY_AUTH_TOKEN=nfp_dJpPEC9kz7XtGdHFQrrUEeLDWAaZgCX5ab9b
npx netlify-cli deploy --prod --no-build --dir=www

# 3. Deploy backend a Vercel
cd /home/fran/CampoEnOrden && vercel --prod
```
