# Deploy del Chatbot (Backend)

## Requisitos

- Node.js (para Vercel CLI)
- Python 3.12+
- Acceso al proyecto en Vercel (ya vinculado en `.vercel/`)

## 1. Hacer cambios en los flows

Los archivos del chatbot están en:

```
backend/campoenorden_backend/chatbot/flows/
├── base.py            # Clase BaseFlow, métodos compartidos
├── fertilizacion.py
├── pulverizacion.py
├── siembra.py
├── cosecha.py
├── combustible.py
├── mantenimiento.py
├── router.py
├── views.py
└── services/
    └── whatsapp.py
```

## 2. Deploy a Vercel

Desde la raíz del proyecto:

```bash
vercel --prod
```

Esto despliega automáticamente usando `vercel.json` que enruta todo a `api/index.py`.

## 3. Token de WhatsApp (gestión simplificada)

### Verificar estado del token

**Opción A — Health endpoint (rápido):**
```bash
curl https://campoenorden-api.vercel.app/api/chatbot/health/
# {"status":"ok","meta_token":"valid"}         ← Token OK
# {"status":"token_error","meta_token":"invalid"}   ← Token expirado
```

**Opción B — Debug endpoint (detallado):**
```bash
curl "https://campoenorden-api.vercel.app/api/chatbot/debug/?action=check_token"
```

**Opción C — Management command (local):**
```bash
python manage.py check_whatsapp_token
# Token OK — 5493512345678
# Token INVALID — error 190: This access token is invalid
```

### Cómo regenerar el token

1. Ir a https://developers.facebook.com → *Meta for Developers* → *WhatsApp* → *Token de acceso temporal*
2. Copiar el token (es el único campo que se ve, no hace falta entrar a nada más)
3. En la terminal:
```bash
vercel env rm WHATSAPP_ACCESS_TOKEN production --yes
# luego pegar el token y presionar Ctrl+D:
vercel env add WHATSAPP_ACCESS_TOKEN production
# redeploy:
vercel --prod
```

> El token dura 60 días desde que se genera. No hace falta App Review ni nada más.

### Auto-refresh automático (no volver a hacer esto nunca más)

Hay un workflow de GitHub Actions en `.github/workflows/refresh-whatsapp-token.yml` que:

1. **Cada 50 días** llama a la Graph API de Facebook para extender el token por otros 60 días
2. Actualiza la env var en Vercel
3. Redeploy automático

**Configurar una sola vez (secrets de GitHub):**

Andá a https://github.com/Cisc0Matic/CampoEnOrden/settings/secrets/actions y agregá estos secrets:

| Secret | Valor |
|---|---|
| `FACEBOOK_APP_ID` | El App ID de Meta Developers |
| `FACEBOOK_APP_SECRET` | El App Secret de Meta Developers |
| `VERCEL_TOKEN` | Token de Vercel (vercel.com/account/tokens) |
| `WHATSAPP_ACCESS_TOKEN` | El token actual de WhatsApp |

Una vez configurado, **nunca más vas a necesitar entrar a Meta Developers**. El workflow se encarga solo.

Para probarlo manualmente: andá a https://github.com/Cisc0Matic/CampoEnOrden/actions → *Refresh WhatsApp Token* → *Run workflow*.

## 4. Verificar el deploy

```bash
curl https://campoenorden-api.vercel.app/api/chatbot/health/
```

## 5. Si el usuario tiene la sesión trabada

Si el usuario ya inició el chatbot y quedó con `awaiting_dni: true` o `user_id: null`:

1. Ir a Neon.tech y borrar la sesión en la tabla `chatbot_whatsappsession`
2. O pedirle al usuario que escriba *MENU*

## 6. Estructura de flows

Cada flow (fertilizacion, pulverizacion, etc.) hereda de `BaseFlow` y define métodos `step_N()`. El router deriva a `step_0` según el `FLOW_NAME`.

Los métodos clave de `BaseFlow`:

| Método | Descripción |
|---|---|
| `_step_ask_campo()` | Muestra lista de campos |
| `_step_process_campo_ask_lote()` | Procesa campo elegido y muestra lotes |
| `_step_process_lote()` | Procesa lote elegido |
| `_interactive_list()` | Envía lista interactiva de WhatsApp |
| `_reply_buttons()` | Envía botones de respuesta rápida |
| `_who_buttons()` | Botones "Personal propio / Contratista" |
| `_yes_no_buttons()` | Botones "Sí / No" |
| `_confirm_buttons()` | Botones "Confirmar / Modificar / Cancelar" |
| `_products_loop()` | Loop de carga de productos (formato: `PRODUCTO - DOSIS/HA - TOTAL`) |
| `_option_list()` | Lista interactiva de opciones |

## 7. Logs de errores

```bash
# Ver errores de producción
vercel logs --environment production --level error --since 1h --expand
```

Los errores aparecen como:
- `WhatsApp send_text API error` → problema de token (corroborar con `curl .../health/`)
- `Flow fertilizacion step 0 error: ...` → error en el código del flow

## 8. Chatbot en funcionamiento

### IDs de mensajes interactivos
- Los IDs de listas y botones son strings numéricos (`"1"`, `"2"`, etc.) para compatibilidad con `_parse_int()` y `_TIPO_MAP`.
- Los mensajes de texto simple se usan solo para fechas, números y texto libre.

### Flujo típico

1. Usuario escribe MENU → `show_main_menu()`
2. Selecciona "Labores" → `get_labores_submenu()`
3. Selecciona tipo (Pulverización, Fertilización, Siembra, Cosecha)
4. Campo → Lote → Fecha → Cultivo → Tipo → Productos → Quién → Observación → Confirmación

### Sesiones
- Cada sesión se identifica por el número de teléfono.
- El estado se guarda en `WhatsAppSession` (step actual + datos).
- Si el chatbot no responde, escribir *MENU* reinicia el flujo.
