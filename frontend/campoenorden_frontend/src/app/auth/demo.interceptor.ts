import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpResponse } from '@angular/common/http';
import { Observable, from, of } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';

@Injectable()
export class DemoInterceptor implements HttpInterceptor {

  constructor(private storage: Storage) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const localStorageToken = localStorage.getItem('jwt_token');
    if (localStorageToken && localStorageToken.startsWith('demo_')) {
      return this.handleDemo(request);
    }

    return from(this.getReadyStorage()).pipe(
      switchMap(storage => from(storage.get('jwt_token'))),
      switchMap(storageToken => {
        if (storageToken && storageToken.startsWith('demo_')) {
          localStorage.setItem('jwt_token', storageToken);
          return this.handleDemo(request);
        }
        return next.handle(request);
      })
    );
  }

  private async getReadyStorage(): Promise<Storage> {
    await this.storage.create();
    return this.storage;
  }

  private handleDemo(request: HttpRequest<any>): Observable<HttpEvent<any>> {
    const url = request.url;

    if (url.endsWith('/token/') && request.method === 'POST') {
      const t = localStorage.getItem('jwt_token');
      return of(new HttpResponse({ status: 200, body: { access: t, refresh: t } }));
    }

    const data = this.getMockData(url, request);
    if (data !== null) {
      return of(new HttpResponse({ status: 200, body: data }));
    }

    return of(new HttpResponse({ status: 200, body: null }));
  }

  // ─── Store ───────────────────────────────────────────────

  private static initialized = false;
  private static store: { [collection: string]: any[] } = {};

  private static readonly SEED: { [collection: string]: any[] } = {
    'core/campos/': [
      { id: 1, nombre: 'San José', ubicacion: 'Ruta 8, Km 120', localidad: 'Bell Ville', provincia: 'Córdoba', productor: 1, productor_nombre: 'Juan Pérez', superficie_total: 450, superficie_trabajada: 350, estado_contrato: 'ACTIVO', margen: 25000, observaciones: 'Campo principal' },
      { id: 2, nombre: 'La Merced', ubicacion: 'Camino a Laboulaye', localidad: 'Laboulaye', provincia: 'Córdoba', productor: 2, productor_nombre: 'María García', superficie_total: 350, superficie_trabajada: 280, estado_contrato: 'ACTIVO', margen: 18000, observaciones: '' },
      { id: 3, nombre: 'El Ombú', ubicacion: 'Ruta 9, Km 200', localidad: 'Marcos Juárez', provincia: 'Córdoba', productor: 3, productor_nombre: 'Carlos López', superficie_total: 400, superficie_trabajada: 220, estado_contrato: 'VENCIDO', margen: 5000, observaciones: 'Contrato a renovar' }
    ],
    'core/lotes/': [
      { id: 1, nombre: 'Lote A', campo: 1, campo_nombre: 'San José', campana: 1, campana_nombre: '2025/2026', cultivo: 1, cultivo_nombre: 'Soja', superficie: 120, activo: true, rendimiento_estimado: 38, precio_tn: 2800 },
      { id: 2, nombre: 'Lote B', campo: 1, campo_nombre: 'San José', campana: 1, campana_nombre: '2025/2026', cultivo: 2, cultivo_nombre: 'Maíz', superficie: 100, activo: true, rendimiento_estimado: 85, precio_tn: 2200 },
      { id: 3, nombre: 'Lote Norte', campo: 2, campo_nombre: 'La Merced', campana: 1, campana_nombre: '2025/2026', cultivo: 1, cultivo_nombre: 'Soja', superficie: 150, activo: true, rendimiento_estimado: 35, precio_tn: 2800 },
      { id: 4, nombre: 'Lote Sur', campo: 2, campo_nombre: 'La Merced', campana: 1, campana_nombre: '2025/2026', cultivo: 3, cultivo_nombre: 'Trigo', superficie: 80, activo: true, rendimiento_estimado: 45, precio_tn: 2400 },
      { id: 5, nombre: 'Lote 3', campo: 3, campo_nombre: 'El Ombú', campana: 2, campana_nombre: '2024/2025', cultivo: 1, cultivo_nombre: 'Soja', superficie: 100, activo: true, rendimiento_estimado: 32, precio_tn: 2600 }
    ],
    'core/labores/': [
      { id: 1, tipo: 'SIEMBRA', tipo_display: 'Siembra', estado: 'APROBADA', estado_display: 'Aprobada', fecha: '2025-10-15', lote: 1, lote_nombre: 'San José', hectareas: 120, precio_por_ha: 45, moneda: 'USD', contratista: 4, contratista_nombre: 'Sembrar SA', responsable: null, responsable_nombre: '', costo_total: 5400, costo_dolares_ha: 45, costo_pesos_ha: null, qq_ha: null, foto_receta: null, foto_receta_url: null, observaciones: 'Siembra directa', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2025-10-15T10:00:00Z', revisada_por: 1, revisada_por_nombre: 'admin', fecha_revision: '2025-10-16T08:00:00Z', sub_tipo_otra: null, sub_tipo_otra_nombre: '', insumos: [] },
      { id: 2, tipo: 'FERTILIZACION_TERRESTRE', tipo_display: 'Fertilización terrestre', estado: 'REVISADA', estado_display: 'Revisada', fecha: '2025-11-20', lote: 1, lote_nombre: 'San José', hectareas: 110, precio_por_ha: 35, moneda: 'USD', contratista: 5, contratista_nombre: 'Fertilizar SRL', responsable: null, responsable_nombre: '', costo_total: 3850, costo_dolares_ha: 35, costo_pesos_ha: null, qq_ha: null, foto_receta: null, foto_receta_url: null, observaciones: '', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2025-11-20T09:00:00Z', revisada_por: null, revisada_por_nombre: '', fecha_revision: null, sub_tipo_otra: null, sub_tipo_otra_nombre: '', insumos: [] },
      { id: 3, tipo: 'PULVERIZACION_TERRESTRE', tipo_display: 'Pulverización terrestre', estado: 'CARGADA', estado_display: 'Cargada', fecha: '2025-12-05', lote: 3, lote_nombre: 'La Merced', hectareas: 140, precio_por_ha: 28, moneda: 'USD', contratista: 4, contratista_nombre: 'Sembrar SA', responsable: null, responsable_nombre: '', costo_total: 3920, costo_dolares_ha: 28, costo_pesos_ha: null, qq_ha: null, foto_receta: null, foto_receta_url: null, observaciones: 'Aplicación de glifosato', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2025-12-05T11:00:00Z', revisada_por: null, revisada_por_nombre: '', fecha_revision: null, sub_tipo_otra: null, sub_tipo_otra_nombre: '', insumos: [
        { id: 1, labor: 3, insumo: 1, insumo_nombre: 'Glifosato', precio_referencia: null, total_aplicado: 140, dosis: 1, dosis_calculada: 1, unidad_dosis: 'lt/ha', precio_unitario: 4.5, costo_total: 630 }
      ]},
      { id: 4, tipo: 'COSECHA', tipo_display: 'Cosecha', estado: 'PENDIENTE_REVISION', estado_display: 'Pendiente de revisión', fecha: '2026-03-10', lote: 1, lote_nombre: 'San José', hectareas: 100, precio_por_ha: 60, moneda: 'USD', contratista: 5, contratista_nombre: 'Fertilizar SRL', responsable: null, responsable_nombre: '', costo_total: 6000, costo_dolares_ha: 60, costo_pesos_ha: null, qq_ha: 38, foto_receta: null, foto_receta_url: null, observaciones: 'Cosecha soja primera', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2026-03-10T14:00:00Z', revisada_por: null, revisada_por_nombre: '', fecha_revision: null, sub_tipo_otra: null, sub_tipo_otra_nombre: '', insumos: [] },
      { id: 5, tipo: 'OTRA', tipo_display: 'Otra', estado: 'CARGADA', estado_display: 'Cargada', fecha: '2026-01-15', lote: 2, lote_nombre: 'San José', hectareas: 80, precio_por_ha: 20, moneda: 'USD', contratista: null, contratista_nombre: '', responsable: null, responsable_nombre: '', costo_total: 1600, costo_dolares_ha: 20, costo_pesos_ha: null, qq_ha: null, foto_receta: null, foto_receta_url: null, observaciones: 'Monitoreo de plagas', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2026-01-15T08:00:00Z', revisada_por: null, revisada_por_nombre: '', fecha_revision: null, sub_tipo_otra: 1, sub_tipo_otra_nombre: 'Monitoreo', insumos: [] },
      { id: 6, tipo: 'SIEMBRA', tipo_display: 'Siembra', estado: 'FACTURADA', estado_display: 'Facturada', fecha: '2025-06-20', lote: 5, lote_nombre: 'El Ombú', hectareas: 100, precio_por_ha: 42, moneda: 'USD', contratista: 4, contratista_nombre: 'Sembrar SA', responsable: null, responsable_nombre: '', costo_total: 4200, costo_dolares_ha: 42, costo_pesos_ha: null, qq_ha: null, foto_receta: null, foto_receta_url: null, observaciones: 'Siembra de soja', cargada_por: 1, cargada_por_nombre: 'admin', fecha_hora_carga: '2025-06-20T09:00:00Z', revisada_por: 1, revisada_por_nombre: 'admin', fecha_revision: '2025-06-21T10:00:00Z', sub_tipo_otra: null, sub_tipo_otra_nombre: '', insumos: [
        { id: 2, labor: 6, insumo: 3, insumo_nombre: 'Semilla Soja', precio_referencia: null, total_aplicado: 2500, dosis: 25, dosis_calculada: 25, unidad_dosis: 'kg/ha', precio_unitario: 1.2, costo_total: 3000 }
      ]}
    ],
    'core/personas/': [
      { id: 1, nombre: 'Juan Pérez', tipo: 'FISICA', rol: 'PRODUCTOR', nombre_rol: 'Productor', documento: '20123456789', cuil: '20-12345678-9', direccion: 'Av. Siempre Viva 742', telefono: '353 4112233', email: 'juan@ejemplo.com', activo: true },
      { id: 2, nombre: 'María García', tipo: 'FISICA', rol: 'PRODUCTOR', nombre_rol: 'Productor', documento: '27987654321', cuil: '27-98765432-1', direccion: 'San Martín 500', telefono: '353 4223344', email: 'maria@ejemplo.com', activo: true },
      { id: 3, nombre: 'Sembrar SA', tipo: 'JURIDICA', rol: 'CONTRATISTA', nombre_rol: 'Contratista', documento: '30765432109', cuil: '30-76543210-9', direccion: 'Ruta 9 Km 180', telefono: '346 8445566', email: 'info@sembrar.com', activo: true },
      { id: 4, nombre: 'Fertilizar SRL', tipo: 'JURIDICA', rol: 'CONTRATISTA', nombre_rol: 'Contratista', documento: '30987654321', cuil: '30-98765432-1', direccion: 'Av. Agricultura 750', telefono: '353 4778899', email: 'ventas@fertilizar.com', activo: true },
      { id: 5, nombre: 'Ing. Carlos López', tipo: 'FISICA', rol: 'INGENIERO', nombre_rol: 'Ingeniero Agrónomo', documento: '18345678901', cuil: '20-34567890-1', direccion: 'Belgrano 300', telefono: '353 4334455', email: 'carlos@ejemplo.com', activo: true }
    ],
    'core/cultivos/': [
      { id: 1, nombre: 'Soja', familia: 'LEGUMINOSA', ciclo: 'GRUESA', activo: true },
      { id: 2, nombre: 'Maíz', familia: 'GRAMINEA', ciclo: 'GRUESA', activo: true },
      { id: 3, nombre: 'Trigo', familia: 'GRAMINEA', ciclo: 'FINA', activo: true }
    ],
    'core/insumos/': [
      { id: 1, nombre: 'Glifosato 48%', tipo: 'AGROQUIMICO', nombre_tipo: 'Agroquímico', unidad: 'lt', activo: true },
      { id: 2, nombre: 'Urea granulada', tipo: 'FERTILIZANTE', nombre_tipo: 'Fertilizante', unidad: 'kg', activo: true },
      { id: 3, nombre: 'Semilla Soja DM 40', tipo: 'SEMILLA', nombre_tipo: 'Semilla', unidad: 'kg', activo: true },
      { id: 4, nombre: 'Atrazina 90%', tipo: 'AGROQUIMICO', nombre_tipo: 'Agroquímico', unidad: 'lt', activo: true },
      { id: 5, nombre: 'Superfosfato triple', tipo: 'FERTILIZANTE', nombre_tipo: 'Fertilizante', unidad: 'kg', activo: true }
    ],
    'core/campanas/': [
      { id: 1, nombre: '2025/2026', fecha_inicio: '2025-06-01', fecha_fin: '2026-05-31', activo: true },
      { id: 2, nombre: '2024/2025', fecha_inicio: '2024-06-01', fecha_fin: '2025-05-31', activo: false }
    ],
    'core/fletes/': [
      { id: 1, nro_cpe: 'CPE-00123', ctg: '12345678', lote: 1, patente_camion: 'ABC123', patente_acoplado: 'XYZ789', chofer: 3, chofer_nombre: 'Sembrar SA', fecha_hora_salida: '2026-03-10T14:00:00Z', fecha_hora_llegada: '2026-03-10T18:30:00Z', peso_origen: 28500, peso_destino: 28300, flete_corto: 2000, flete_largo: null, comision: 500, secada: 300, cosecha: null, costo_comercial: 200, destino: 'Acopio Central Bell Ville', observaciones: '', estado: 'ENTREGADO', estado_display: 'Entregado' },
      { id: 2, nro_cpe: 'CPE-00124', ctg: '87654321', lote: 3, patente_camion: 'DEF456', patente_acoplado: 'UVW321', chofer: 4, chofer_nombre: 'Fertilizar SRL', fecha_hora_salida: '2026-03-15T08:00:00Z', fecha_hora_llegada: null, peso_origen: 31000, peso_destino: null, flete_corto: 2500, flete_largo: 3500, comision: 600, secada: 400, cosecha: null, costo_comercial: 250, destino: 'Puerto Rosario', observaciones: 'En tránsito', estado: 'EN_TRASLADO', estado_display: 'En Traslado' },
      { id: 3, nro_cpe: 'CPE-00125', ctg: '11223344', lote: 5, patente_camion: 'GHI789', patente_acoplado: 'RST654', chofer: 3, chofer_nombre: 'Sembrar SA', fecha_hora_salida: '2026-02-20T10:00:00Z', fecha_hora_llegada: '2026-02-20T15:00:00Z', peso_origen: 26500, peso_destino: 26400, flete_corto: 1800, flete_largo: null, comision: 450, secada: 250, cosecha: null, costo_comercial: 180, destino: 'Cooperativa Marcos Juárez', observaciones: '', estado: 'ENTREGADO', estado_display: 'Entregado' }
    ],
    'core/documentos/': [
      { id: 1, tipo: 'CONTRATO', tipo_display: 'Contrato', numero: 'CONT-2025-001', campo: 1, campo_nombre: 'San José', labor: null, flete: null, titular: 1, titular_nombre: 'Juan Pérez', archivo: null, archivo_url: null, observaciones: 'Contrato anual campaña 2025/2026', estado: 'APROBADO', estado_display: 'Aprobado', fecha_documento: '2025-05-01', fecha_vencimiento: '2026-05-31', monto: 45000 },
      { id: 2, tipo: 'FACTURA', tipo_display: 'Factura', numero: 'F-00123', campo: 1, campo_nombre: 'San José', labor: 1, flete: null, titular: 4, titular_nombre: 'Sembrar SA', archivo: null, archivo_url: null, observaciones: 'Siembra lote A', estado: 'PENDIENTE', estado_display: 'Pendiente de Revisar', fecha_documento: '2025-10-15', fecha_vencimiento: '2025-11-15', monto: 5400 },
      { id: 3, tipo: 'FACTURA', tipo_display: 'Factura', numero: 'F-00124', campo: 2, campo_nombre: 'La Merced', labor: 2, flete: null, titular: 5, titular_nombre: 'Fertilizar SRL', archivo: null, archivo_url: null, observaciones: '', estado: 'VENCIDO', estado_display: 'Vencido', fecha_documento: '2025-11-20', fecha_vencimiento: '2025-12-20', monto: 3850 }
    ],
    'core/parametros/': [
      { id: 1, nombre: 'Soja Precio TN', categoria: 'GRANO', categoria_display: 'Granos', valor: 2800, unidad: 'USD/tn', campana: 1, campana_nombre: '2025/2026', vigente: true },
      { id: 2, nombre: 'Maíz Precio TN', categoria: 'GRANO', categoria_display: 'Granos', valor: 2200, unidad: 'USD/tn', campana: 1, campana_nombre: '2025/2026', vigente: true },
      { id: 3, nombre: 'Trigo Precio TN', categoria: 'GRANO', categoria_display: 'Granos', valor: 2400, unidad: 'USD/tn', campana: 1, campana_nombre: '2025/2026', vigente: true },
      { id: 4, nombre: 'Glifosato Precio', categoria: 'INSUMO', categoria_display: 'Insumos', valor: 4.5, unidad: 'USD/lt', campana: null, campana_nombre: null, vigente: true },
      { id: 5, nombre: 'Tipo de Cambio Oficial', categoria: 'TIPO_CAMBIO', categoria_display: 'Tipo de Cambio', valor: 1200, unidad: 'ARS/USD', campana: null, campana_nombre: null, vigente: true }
    ],
    'core/productos-precio/': [
      { id: 1, insumo: 1, insumo_nombre: 'Glifosato 48%', precio_unitario: 4.5, moneda: 'USD', proveedor: 4, proveedor_nombre: 'Fertilizar SRL', fecha_precio: '2025-11-01', vigencia_desde: null, vigencia_hasta: null, observaciones: '' },
      { id: 2, insumo: 3, insumo_nombre: 'Semilla Soja DM 40', precio_unitario: 1.2, moneda: 'USD', proveedor: 3, proveedor_nombre: 'Sembrar SA', fecha_precio: '2025-09-01', vigencia_desde: null, vigencia_hasta: null, observaciones: 'Precio por kg' }
    ],
    'core/tipos-labor-personalizado/': [
      { id: 1, nombre: 'Monitoreo', activo: true },
      { id: 2, nombre: 'Labranza', activo: true },
      { id: 3, nombre: 'Rolado', activo: true },
      { id: 4, nombre: 'Limpieza de alambrado', activo: true }
    ]
  };

  private static initStore(): void {
    if (DemoInterceptor.initialized) return;
    for (const [collection, data] of Object.entries(DemoInterceptor.SEED)) {
      DemoInterceptor.store[collection] = data.map(item => ({ ...item }));
    }
    DemoInterceptor.initialized = true;
  }

  // ─── Mock data router ────────────────────────────────────

  private getMockData(url: string, request: HttpRequest<any>): any {
    DemoInterceptor.initStore();

    if (request.method === 'GET') {
      return this.handleGET(url);
    }
    if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
      return this.handleWrite(request.method as 'POST' | 'PUT' | 'PATCH', url, request);
    }
    if (request.method === 'DELETE') {
      return this.handleDelete(url);
    }
    return null;
  }

  private handleGET(url: string): any {
    const path = this.extractPath(url);

    if (path === 'core/dashboard/') {
      return {
        campos_activos: 8, hectareas_totales: 1200, hectareas_trabajadas: 850,
        labores_cargadas: 45, costos_totales: 125000, costos_por_ha: 147.06,
        documentos_pendientes: 3,
        alertas: ['1 campo(s) con contrato vencido(s)', '2 documento(s) vencido(s)']
      };
    }

    if (path === 'core/dashboard/margen/' || path.startsWith('core/dashboard/margen/')) {
      return {
        conceptos: [
          { concepto: 'Insumos', usd_total: 45000, usd_ha: 52.94, porc_costo_total: 36.0 },
          { concepto: 'Labores', usd_total: 38000, usd_ha: 44.71, porc_costo_total: 30.4 },
          { concepto: 'Cosecha', usd_total: 22000, usd_ha: 25.88, porc_costo_total: 17.6 },
          { concepto: 'Comercialización', usd_total: 20000, usd_ha: 23.53, porc_costo_total: 16.0 }
        ],
        total_costos_variables: 125000, ingreso_bruto: 185000, margen_bruto: 60000,
        costo_directo_alquiler: 15000, margen_bruto_directo: 45000,
        rentabilidad_roi: 48.0, hectareas: 850
      };
    }

    const parsed = this.parsePath(path);
    if (!parsed) return null;

    if (parsed.id !== undefined) {
      const items = DemoInterceptor.store[parsed.collection] || [];
      return items.find(item => item.id === parsed.id) || null;
    }

    return DemoInterceptor.store[parsed.collection] || [];
  }

  private handleWrite(method: 'POST' | 'PUT' | 'PATCH', url: string, request: HttpRequest<any>): any {
    const path = this.extractPath(url);
    const parsed = this.parsePath(path);

    if (!parsed) {
      return { ...request.body, id: Math.floor(Math.random() * 10000), success: true };
    }

    if (method === 'POST') {
      if (!DemoInterceptor.store[parsed.collection]) {
        DemoInterceptor.store[parsed.collection] = [];
      }
      const items = DemoInterceptor.store[parsed.collection];
      const maxId = items.reduce((max, item) => Math.max(max, item.id || 0), 0);
      const newItem = { ...request.body, id: maxId + 1 };
      items.push(newItem);
      return newItem;
    }

    const items = DemoInterceptor.store[parsed.collection] || [];
    const index = items.findIndex(item => item.id === parsed.id);
    if (index !== -1) {
      items[index] = { ...items[index], ...request.body };
      return items[index];
    }

    return { ...request.body, id: parsed.id, success: true };
  }

  private handleDelete(url: string): any {
    const path = this.extractPath(url);
    const parsed = this.parsePath(path);
    if (parsed && parsed.id !== undefined) {
      const items = DemoInterceptor.store[parsed.collection] || [];
      DemoInterceptor.store[parsed.collection] = items.filter(item => item.id !== parsed.id);
    }
    return { success: true };
  }

  // ─── URL helpers ─────────────────────────────────────────

  private extractPath(url: string): string {
    const match = url.match(/\/api\/(.+?)(\?|$)/);
    return match ? match[1] : '';
  }

  private parsePath(path: string): { collection: string; id?: number } | null {
    const detailMatch = path.match(/^(.+\/)(\d+)\/$/);
    if (detailMatch) {
      return { collection: detailMatch[1], id: parseInt(detailMatch[2], 10) };
    }
    const collectionMatch = path.match(/^(.+\/)$/);
    if (collectionMatch) {
      return { collection: collectionMatch[1] };
    }
    return null;
  }
}
