# Usuarios de prueba y contraseñas

## Locales (desarrollo) — BD `backend/campoenorden_backend/db.sqlite3`

Contraseña común: `Test.2026`

| username | rol | notas |
|----------|-----|-------|
| `admin_test` | Admin Principal | german · tel. 5493515999981 |
| `operario_test` | Operario | juan · tel. 5491198765432 |
| `German01` | Operario | german |

## Producción — contenedor `campoenorden-db` (VPS 149.50.130.161)

| username | rol | contraseña | notas |
|----------|-----|------------|-------|
| `admin` | Admin Principal · superuser | `AgNhYwo8KB127ndp` | `admin@campoenorden.local` — acceso `/admin/` |
| `empresa_test` | Admin de Empresa | `YABFnIvn18TV8o4l` | empresa: "Campo barr" · `campoenorden2026+empresa@gmail.com` |

### Usuarios de producción sin contraseña conocida

| username | rol | activo | notas |
|----------|-----|--------|-------|
| `produser1` | Operario | sí | dni 19372727 (teléfono 5493511000001) |
| `Francis` | Operario | sí | Francis Barrionuevo · dni 43813147 · +5491156567570 |
| `testuser99` | Operario | no | usuario desactivado |
| `verceltest1` | Operario | no | usuario desactivado |

> Las contraseñas solo se guardan hasheadas (PBKDF2); las de arriba son las únicas que existen en claro porque fueron generadas/reseteadas al crear estas cuentas de test.