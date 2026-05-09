export interface Labor {
  id: number;
  tipo: string;
  tipo_display: string;
  estado: string;
  estado_display: string;
  fecha: string;
  lote: number;
  lote_nombre: string;
  hectareas: number;
  precio_por_ha: number;
  moneda: string;
  contratista: number | null;
  contratista_nombre: string;
  responsable: number | null;
  responsable_nombre: string;
  costo_total: number;
  costo_dolares_ha: number;
  costo_pesos_ha: number;
  qq_ha: number;
  foto_receta: string | null;
  foto_receta_url: string | null;
  observaciones: string;
  cargada_por: number | null;
  cargada_por_nombre: string;
  fecha_hora_carga: string;
  revisada_por: number | null;
  revisada_por_nombre: string;
  fecha_revision: string | null;
  sub_tipo_otra: number | null;
  sub_tipo_otra_nombre: string;
  insumos: LaborInsumo[];
}

export interface LaborInsumo {
  id: number;
  labor: number;
  insumo: number;
  insumo_nombre: string;
  precio_referencia: number | null;
  total_aplicado: number;
  dosis: number;
  dosis_calculada: number;
  unidad_dosis: string;
  precio_unitario: number;
  costo_total: number;
}

export interface Insumo {
  id: number;
  nombre: string;
  tipo: string;
  nombre_tipo: string;
  unidad: string;
  activo: boolean;
}

export interface ProductoPrecio {
  id: number;
  insumo: number;
  insumo_nombre: string;
  precio_unitario: number;
  moneda: string;
  proveedor: number | null;
  proveedor_nombre: string;
  fecha_precio: string;
  vigencia_desde: string | null;
  vigencia_hasta: string | null;
  observaciones: string;
}

export interface TipoLaborPersonalizado {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface Campo {
  id: number;
  nombre: string;
  ubicacion: string;
  localidad: string;
  provincia: string;
  productor: number | null;
  productor_nombre: string;
  superficie_total: number;
  estado_contrato: string;
  observaciones: string;
}

export interface Lote {
  id: number;
  nombre: string;
  campo: number;
  campo_nombre: string;
  campana: number;
  campana_nombre: string;
  cultivo: number;
  cultivo_nombre: string;
  superficie: number;
  activo: boolean;
}

export interface Persona {
  id: number;
  nombre: string;
  tipo: string;
  rol: string;
  nombre_rol: string;
  telefono: string;
  email: string;
  activo: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  role_display: string;
  telefono: string;
  empresa: number | null;
}

export interface MargenData {
  conceptos: MargenConcepto[];
  total_costos_variables: number;
  ingreso_bruto: number;
  margen_bruto: number;
  costo_directo_alquiler: number;
  margen_bruto_directo: number;
  rentabilidad_roi: number;
  hectareas: number;
}

export interface MargenConcepto {
  concepto: string;
  usd_total: number;
  usd_ha: number;
  porc_costo_total: number;
}

export const TIPOS_LABOR = [
  { value: 'SIEMBRA', label: 'Siembra' },
  { value: 'PULVERIZACION_TERRESTRE', label: 'Pulverización terrestre' },
  { value: 'PULVERIZACION_DRONES', label: 'Pulverización con drones' },
  { value: 'PULVERIZACION_AEREA', label: 'Pulverización aérea' },
  { value: 'FERTILIZACION_TERRESTRE', label: 'Fertilización terrestre' },
  { value: 'FERTILIZACION_DRONES', label: 'Fertilización con drones' },
  { value: 'COSECHA', label: 'Cosecha' },
  { value: 'OTRA', label: 'Otra' },
];

export const ESTADOS_LABOR = [
  { value: 'CARGADA', label: 'Cargada' },
  { value: 'PENDIENTE_REVISION', label: 'Pendiente de revisión' },
  { value: 'REVISADA', label: 'Revisada' },
  { value: 'APROBADA', label: 'Aprobada' },
  { value: 'PENDIENTE_FACTURA', label: 'Pendiente de facturar' },
  { value: 'FACTURADA', label: 'Facturada' },
  { value: 'COBRADA', label: 'Cobrada' },
];

export function getTipoIcon(tipo: string): string {
  switch (tipo) {
    case 'SIEMBRA': return 'leaf';
    case 'PULVERIZACION_TERRESTRE':
    case 'PULVERIZACION_DRONES':
    case 'PULVERIZACION_AEREA': return 'water';
    case 'FERTILIZACION_TERRESTRE':
    case 'FERTILIZACION_DRONES': return 'flask';
    case 'COSECHA': return 'grid';
    default: return 'construct';
  }
}

export function getEstadoColor(estado: string): string {
  switch (estado) {
    case 'CARGADA': return 'medium';
    case 'PENDIENTE_REVISION': return 'warning';
    case 'REVISADA': return 'primary';
    case 'APROBADA': return 'success';
    case 'PENDIENTE_FACTURA': return 'tertiary';
    case 'FACTURADA': return 'dark';
    case 'COBRADA': return 'success';
    default: return 'medium';
  }
}
