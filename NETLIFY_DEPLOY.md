# Instrucciones para despliegue en Netlify

## Estructura del proyecto para Netlify

```
CampoEnOrden/
├── netlify.toml          # Configuración de Netlify (en la raíz)
├── frontend/
│   └── campoenorden_frontend/
│       ├── angular.json
│       ├── package.json
│       ├── src/
│       └── (archivos del proyecto Angular)
└── (otros directorios: backend/, docs/, etc.)
```

## Configuración de netlify.toml

```toml
[build]
  base = "frontend/campoenorden_frontend"
  command = "npm install --include=dev && npm run build"
  publish = "www"

[build.environment]
  NODE_VERSION = "20"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**Puntos clave:**
- `base`: Directorio donde está el proyecto Angular
- `NODE_VERSION = "20"`: Angular 20 requiere Node.js 20+
- `--include=dev`: Necesario para instalar devDependencies (@angular/cli, etc.)
- `publish = "www"`: Directorio de salida del build (relativo a `base`)

## Crear ZIP para despliegue manual

```bash
cd /home/fran/CampoEnOrden && \
rm -f CampoEnOrDen-Netlify.zip && \
zip -r CampoEnOrDen-Netlify.zip . \
  -x "backend/*" "docs/*" ".git/*" "*.sh" "*.ps1" "*.md" \
  "frontend/campoenorden_frontend/node_modules/*" \
  "frontend/campoenorden_frontend/.angular/*" \
  "frontend/campoenorden_frontend/www/*" \
  "frontend/campoenorden_frontend/ios/*" \
  "frontend/campoenorden_frontend/android/*" \
  "frontend/campoenorden_frontend/package-lock.json"
```

## Pasos en Netlify UI

1. **Desactivar plugin de Angular** (opcional pero recomendado):
   - Ve a **Integrations** en Netlify UI
   - Busca "@netlify/angular-runtime" y desactívalo

2. **Configurar variables de entorno** (si es necesario):
   - **Site settings** → **Build & deploy** → **Environment**
   - Asegúrate de que `NODE_VERSION` esté configurado a `20`

3. **Limpiar caché y redespliegar**:
   - Ve a **Deploys** → **Clear cache and trigger deploy**
   - O sube el nuevo ZIP manualmente

## Actualizar URL del backend

Antes de desplegar, actualiza `frontend/campoenorden_frontend/src/environments/environment.prod.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://TU-BACKEND-REAL.onrender.com/api'
};
```

## Solución de problemas comunes

### Error: "ng: not found"
- Causa: Las devDependencies no se instalaron
- Solución: Usa `npm install --include=dev` en el comando de build

### Error: "Unsupported engine" (Node version)
- Causa: Angular 20 requiere Node.js 20+
- Solución: Configura `NODE_VERSION = "20"` en netlify.toml

### Error de CORS
- Causa: El backend no permite solicitudes desde el dominio de Netlify
- Solución: Configura CORS en el backend para permitir el origen de Netlify
