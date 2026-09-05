# Plan de Implementación — WhatsApp Cloud API a Producción

> Estado: en curso — 05/09/2026. Dueño: CampoEnOrden.

## 1. Objetivo

Llevar el chatbot de WhatsApp (Cloud API de Meta) de la **versión de prueba**
(Test Number) a **producción** con un número real de Argentina, HTTPS definitivo y
operación segura/monitoreable.

**Meta cambia su pricing el 01/10/2026** → cargar método de pago **antes del
30/09/2026** o dejan de entregar respuestas de servicio.

## 2. Estado actual (05/09/2026)

| Componente | Valor |
|---|---|
| Backend | Django + gunicorn, VPS `149.50.130.161` (systemd `campoenorden`, `127.0.0.1:8000`) |
| Frontend | Netlify `https://campoenorden.netlify.app` |
| HTTPS API | Provisorio: quick tunnel `cloudflared-campoenorden` → `https://<random>.trycloudflare.com` (cambia en cada reinicio) |
| Webhook | Registrado en app `1523301969430270` (callback → túnel, verify `campoenorden_webhook_2026`) |
| Número | **Test Number** `+1 555-656-7570` (gratis, máx. ~5 destinatarios, NO producción) |
| Token | System user de la app, permanente (`expires_at: 0`) |
| E2E | Verificado: HOLA → DNI → menús → flujos; firma `X-Hub-Signature-256` OK |

## 3. Costos (fijar expectativa)

| Ítem | Costo |
|---|---|
| Cloud API (acceso) | USD 0 (integración directa a Graph, sin BSP) |
| Respuestas **service** (usuario inicia, ventana 24 h) | USD 0 hasta el 30/09/2026. Desde el 01/10: **1.000 gratis/mes/número**; exceso a tarifa AR (≈ ARS 37,68 ≈ USD 0,03 c/u) |
| Plantillas outbound (no se usan hoy) | Marketing ≈ ARS 89,56 / Utility ≈ ARS 37,68 por mensaje (rate card AR, 01/07/2026) |
| Verificación de negocio | USD 0 |
| Verificación de número (SMS/llamada) | fee one-off chico/regional (confirmar rate card) |
| Método de pago en Meta | obligatorio cargar **antes del 30/09/2026** |

Regla práctica: el bot responde ~3–5 mensajes por conversación → 1.000 msgs/mes
≈ 200–300 conversaciones sin costo. Superar eso (o arrancar conversaciones vos con
plantillas) es lo único que genera factura.

## 4. Prequisitos del cliente (Meta)

- [ ] Número móvil AR **real y nuevo** (sin uso en WhatsApp) para producción.
- [ ] Documentación de la empresa para **verificación del negocio** (CUIT/Razón Social).
- [ ] **Tarjeta de crédito** como método de pago en el Business Manager (deadline 30/09).
- [ ] **Dominio** para el API definitivo (recomendado: `api.<dominio>` sobre
      `unnuevosantigo.online`, que ya se usa con el tunnel de Odoo).
- [ ] Usuario admin operativo en Business Manager / Meta Developers.

## 5. Fases

### Fase A — Preparación Meta (arrancar YA por el deadline)
1. Verificación de negocio en el Business Manager.
2. Definir/comprar dominio para el API.
3. Cargar método de pago en Meta (deadline 30/09/2026).

### Fase B — HTTPS definitivo (reemplaza el quick tunnel)
1. Cloudflare **named tunnel**: hostname `api.unnuevosantigo.online` →
   `http://127.0.0.1:8000` (mismo patrón que `odoo-odoo`).
2. Config estática del tunnel en el server (sin URL aleatoria); update
   stop/disable del quick tunnel.
   - Alternativa sin Cloudflare: certbot + nginx con cert del dominio directo al VPS.
3. `.env`: `ALLOWED_HOSTS` += `api.unnuevosantigo.online`;
   `DJANGO_HTTPS=1` (con `SECURE_SSL_REDIRECT` env-gated, ver Fase F);
   `FRONTEND_URL`/`CORS` siguen apuntando a Netlify.
4. Desaparece la dependencia del redeploy de Netlify por cambio de URL.

### Fase C — Número de producción en Meta
1. Alta del número AR en la WABA (nombre de display = razón social, requiere aprobación).
2. Verificación del número (código SMS/llamada).
3. Obtener el nuevo `WHATSAPP_PHONE_NUMBER_ID`.
4. Confirmar que el token system user alcanza al nuevo número (perms
   `whatsapp_business_*` + `appsecret_proof` — ya lo exige la app).

### Fase D — Reconfigurar backend
1. `.env`: `WHATSAPP_PHONE_NUMBER_ID` ← nuevo.
2. `systemctl restart campoenorden` + `manage.py check_whatsapp_token` → muestra número nuevo.
3. Health/challenge por la URL definitiva.

### Fase E — Re-registrar webhook en Meta
1. `POST /{app-id}/subscriptions` con `callback_url = https://api.<dominio>/api/chatbot/webhook/`
   (reusar script de `deploy_donweb.md`).
2. Verificar challenge → `test123`.
3. E2E completo (HOLA desde teléfono real).

### Fase F — Seguridad y limpieza (ya en ejecución, 05/09/2026)
1. **Proteger `/api/chatbot/debug/`** (exponía usuarios con DNI/teléfono y `fix_session`).
   → Gate por header `X-Debug-Key` (env `DEBUG_API_KEY`).
2. **Eliminar riesgo del cron de refresh de token**: el script
   `refresh_whatsapp_token.sh` hacía `fb_exchange_token` sobre un token system-user
   permanente → en ~50 días podía reemplazarlo por uno inválido. Reemplazado por un
   **check no destructivo** semanal (solo valida y loguea).
3. **`SECURE_SSL_REDIRECT` env-gated** en `production.py` (`DJANGO_HTTPS`),
   alineando código con la doc. Hoy funciona por el túnel con `X-Forwarded-Proto: https`.
4. Actualizar `deploy_donweb.md` (URL definitiva, número real, precios, gate debug).
5. Confirmar modo dev → **live** de la app al conectar el número real.

### Fase G — Monitoreo y costo
1. Medir mensajes `OUT` por mes (`chatbot_whatsappmessage`) contra el free tier de 1.000.
2. (Opcional) revisar `pricing.billable` en webhooks de status.
3. Alerta del health + check semanal del token.

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| 01/10/2026: respuestas service pagas + payment obligatorio | Tarjeta antes del 30/09; mantenerse bajo 1.000 msgs/mes |
| Test Number sigue activo con usuarios reales | Cutover coordinado al número real; avisar a usuarios |
| App en modo dev o negocio sin verificar | Verificación de negocio antes de vincular número real |
| URL efímera del túnel | Reemplazada en Fase B por hostname fijo |
| `/debug/` público | Fase F (X-Debug-Key) |
| Cron refresh rompe token | Fase F (check no destructivo) |

## 7. Orden recomendado
1. Fase A (prequisitos Meta) — YA por el deadline.
2. Fase F (seguridad) — en curso, no bloquea.
3. Fase B → C → D → E en el cutover.
4. Fase G como operación.

## 8. Criterios de éxito
- E2E real (HOLA → flujo) contra el número AR de producción.
- Webhook con dominio propio; sin dependencia de `trycloudflare`.
- `/debug/` cerrado; cron no destructivo.
- Costo mensual proyectado documentado en `deploy_donweb.md`.