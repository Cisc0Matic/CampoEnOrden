# Diagrama de Base de Datos - CampoEnOrden

## Estructura del Proyecto

```
campoenorden_backend/
├── campenorden/          # Configuración principal
├── core/                # Modelos principales
├── users/               # Usuarios y auth
├── logistica/           # API de fletes
├── mujeres/             # (no usado)
└── laborales/          # (no usado)
```

## Modelos y Relaciones

| Modelo | Descripción | Relaciones |
|--------|-------------|------------|
| **Campo** | Campo física | tiene Lotes, Documentos |
| **Persona** | Personas (dueños, arrendatarios, contratistas) | roles múltiples |
| **Campana** | Campaña agrícola | tiene Lotes, Parámetros |
| **Lote** | Lote dentro de un campo | tiene Labores, Fletes |
| **Cultivo** | Tipo de cultivo | tiene Lotes |
| **Insumo** | Insumos agrícolas | usa en Labores |
| **Labor** | Labor realizada en lote | usa Insumos, tiene Docs |
| **Flete** | Flete de cereal | tiene Documentos |
| **Documento** | Documentos varios | asociado a Campo/Labor/Flete |
| **Parametro** | Parámetros configurables | por Campana |

## Detalle de Campos por Modelo

### Campo
- `nombre` (unique)
- `ubicacion`
- `superficie_total`, `superficie_trabajada`
- `estado_contrato` (ACTIVO/VENCIDO/PENDIENTE/RENOVADO)
- `costo_total`, `costo_por_ha`, `margen`
- `alquiler_pendiente`
- `condiciones_alquiler`

### Persona
- `nombre`
- `tipo` (PERSONA/EMPRESA)
- `rol` (DUENO/ARRENDATARIO/CONTRATISTA/CHOFER/ADMINISTRADOR)
- `documento`, `cuil`, `telefono`, `email`

### Lote
- `campo` (FK)
- `campana` (FK)
- `cultivo` (FK)
- `superficie`
- `rendimiento_estimado`
- `precio_tn`, `tipo_cambio`

### Labor
- `lote` (FK)
- `tipo` (PULVERIZACION/SIEMBRA/FERTILIZACION/COSECHA)
- `fecha`
- `hectareas`
- `costo_dolares_ha`, `costo_pesos_ha`
- `qq_ha`, `costo_total`

### Flete
- `nro_cpe` (unique)
- `lote` (FK)
- `patente_camion`, `patente_acoplado`
- `chofer` (FK)
- `peso_origen`, `peso_destino`
- `flete_corto`, `flete_largo`
- `estado` (PENDIENTE/EN_TRASLADO/ENTREGADO/FACTURADO)

---

```mermaid
erDiagram
  USUARIO {
    int id PK
    string username UK
    string email
    string password
    datetime last_login
    boolean is_active
  }

  CAMPO {
    int id PK
    string nombre UK
    string ubicacion
    decimal superficie_total
    decimal superficie_trabajada
    string condiciones_alquiler
    string estado_contrato
    text observaciones
    decimal costo_total
    decimal costo_por_ha
    decimal margen
    decimal alquiler_pendiente
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  PERSONA {
    int id PK
    string nombre
    string tipo
    string rol
    string documento
    string cuil
    string direccion
    string telefono
    string email
    text observaciones
    boolean activo
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  CAMPANA {
    int id PK
    string nombre
    date inicio
    date fin
    boolean activa
  }

  LOTE {
    int id PK
    int campo_id FK
    int campana_id FK
    string nombre
    int cultivo_id FK
    decimal superficie
    decimal rendimiento_estimado
    decimal precio_tn
    decimal tipo_cambio
    string ubicacion
    boolean activo
    text observaciones
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  CULTIVO {
    int id PK
    string nombre UK
    string abreviatura
    string familia
    boolean activo
  }

  INSUMO {
    int id PK
    string nombre UK
    string tipo
    string unidad
    boolean activo
  }

  LABOR {
    int id PK
    int lote_id FK
    string tipo
    date fecha
    int contratista_id FK
    decimal hectareas
    text observaciones
    decimal costo_dolares_ha
    decimal costo_pesos_ha
    decimal qq_ha
    decimal costo_total
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  LABOR_INSUMO {
    int id PK
    int labor_id FK
    int insumo_id FK
    decimal dosis
    string unidad_dosis
    decimal total_aplicado
    decimal precio_unitario
    decimal costo_total
  }

  FLETE {
    int id PK
    string nro_cpe UK
    string ctg
    int lote_id FK
    string patente_camion
    string patente_acoplado
    int chofer_id FK
    datetime fecha_hora_salida
    datetime fecha_hora_llegada
    decimal peso_origen
    decimal peso_destino
    decimal flete_corto
    decimal flete_largo
    decimal comision
    decimal secada
    decimal cosecha
    decimal costo_comercial
    string destino
    text observaciones
    string estado
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  DOCUMENTO {
    int id PK
    string tipo
    string numero UK
    int campo_id FK
    int labor_id FK
    int flete_id FK
    int titular_id FK
    file archivo
    text observaciones
    string estado
    date fecha_documento
    date fecha_vencimiento
    decimal monto
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  PARAMETRO {
    int id PK
    string nombre
    string categoria
    decimal valor
    string unidad
    int campana_id FK
    boolean vigente
    text observaciones
    date fecha_vigencia_desde
    date fecha_vigencia_hasta
    datetime fecha_creacion
    datetime fecha_modificacion
  }

  %% Relaciones
  USUARIO ||--o{ CAMPO : "gestiona"
  CAMPO ||--o{ LOTE : "contiene"
  CAMPO ||--o{ DOCUMENTO : "asocia"
  CAMPO }o--o{ PERSONA : "locatarios"
  CAMPO }o--o{ PERSONA : "locadores"
  LOTE ||--o{ LABOR : "tiene"
  LOTE ||--o{ FLETE : "tiene"
  LOTE }o--o{ CULTIVO : "cultiva"
  LABOR ||--o{ LABOR_INSUMO : "usa"
  LABOR ||--o{ DOCUMENTO : "documenta"
  LABOR_INSUMO }o--|| INSUMO : "aplica"
  FLETE ||--o{ DOCUMENTO : "documenta"
  FLETE }o--|| PERSONA : "chofer"
  PERSONA }o--o{ DOCUMENTO : "titular"
  CAMPANA ||--o{ LOTE : "abarca"
  CAMPANA ||--o{ PARAMETRO : "define"