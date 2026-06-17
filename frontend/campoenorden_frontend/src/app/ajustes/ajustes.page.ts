import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';
import { HttpParams } from '@angular/common/http';
import { forkJoin } from 'rxjs';

interface Parametro {
  id: number;
  nombre: string;
  categoria: string;
  categoria_display: string;
  valor: number;
  unidad: string;
  campana_nombre: string;
  campana_id: number;
  vigente: boolean;
  fecha_actualizacion: string;
}

interface Campana {
  id: number;
  nombre: string;
}

@Component({
  selector: 'app-ajustes',
  templateUrl: './ajustes.page.html',
  styleUrls: ['./ajustes.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class AjustesPage {
  parametros: Parametro[] = [];
  parametrosFiltrados: Parametro[] = [];
  campanas: Campana[] = [];
  loading = true;
  error: string | null = null;
  categorias: string[] = ['GRANO', 'INSUMO', 'LABOR', 'COMERCIALIZACION', 'COSECHA', 'TIPO_CAMBIO', 'UNIDAD'];
  categoriaSeleccionada: string = '';
  filtroCampana = '';
  mostrarHistorial = false;
  parametroSeleccionado: Parametro | null = null;
  historial: Parametro[] = [];

  constructor(private api: ApiService, private router: Router) {}

  ionViewWillEnter() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    forkJoin({
      campanas: this.api.get<Campana[]>('core/campanas/'),
      parametros: this.api.get<Parametro[]>('core/parametros/')
    }).subscribe({
      next: ({ campanas, parametros }) => {
        this.campanas = campanas || [];
        this.parametros = parametros || [];
        this.filtrarParametros();
        this.loading = false;
      },
      error: () => {
        this.error = 'Error al cargar datos';
        this.loading = false;
      }
    });
  }

  cargarParametros() {
    this.loading = true;
    let path = 'core/parametros/';
    const params = [];
    if (this.categoriaSeleccionada) params.push(`categoria=${this.categoriaSeleccionada}`);
    if (this.filtroCampana) params.push(`campana=${this.filtroCampana}`);
    if (params.length > 0) path += '?' + params.join('&');
    
    this.api.get<Parametro[]>(path).subscribe({
      next: (data) => {
        this.parametros = data || [];
        this.filtrarParametros();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar parámetros';
        this.loading = false;
      }
    });
  }

  filtrarParametros() {
    this.parametrosFiltrados = this.parametros.filter(p => {
      if (this.categoriaSeleccionada && p.categoria !== this.categoriaSeleccionada) return false;
      if (this.filtroCampana && p.campana_id?.toString() !== this.filtroCampana) return false;
      return true;
    });
  }

  filtrarPorCategoria(cat: string) {
    this.categoriaSeleccionada = this.categoriaSeleccionada === cat ? '' : cat;
    this.cargarParametros();
  }

  filtrarPorCampana(campana: string) {
    this.filtroCampana = this.filtroCampana === campana ? '' : campana;
    this.cargarParametros();
  }

  getCategoriaLabel(cat: string): string {
    const labels: { [key: string]: string } = {
      'GRANO': 'Granos',
      'INSUMO': 'Insumos',
      'LABOR': 'Labores',
      'COMERCIALIZACION': 'Comercialización',
      'COSECHA': 'Cosecha',
      'TIPO_CAMBIO': 'Tipo Cambio',
      'UNIDAD': 'Unidades'
    };
    return labels[cat] || cat;
  }

  agregarParametro() {
    this.router.navigate(['/tabs/ajustes/crear']);
  }

  editarParametro(param: any) {
    this.router.navigate(['/tabs/ajustes/editar', param.id]);
  }

  verHistoria(param: any) {
    this.router.navigate(['/tabs/ajustes/crear'], {
      queryParams: { nombre: param.nombre, categoria: param.categoria } 
    });
  }

  nuevaVersion(param: any) {
    this.router.navigate(['/tabs/ajustes/crear'], {
      queryParams: { nombre: param.nombre, categoria: param.categoria, nueva: 'true' } 
    });
  }

  verHistorial(param: Parametro) {
    this.parametroSeleccionado = param;
    this.mostrarHistorial = true;
    this.cargarHistorial(param.nombre, param.categoria);
  }

  cerrarHistorial() {
    this.mostrarHistorial = false;
    this.parametroSeleccionado = null;
    this.historial = [];
  }

  cargarHistorial(nombre: string, categoria: string) {
    const params = new HttpParams()
      .set('nombre', nombre)
      .set('categoria', categoria);
    this.api.get<Parametro[]>('core/parametros/', { params }).subscribe({
      next: (data) => {
        this.historial = data || [];
      },
      error: () => console.error('Error cargando historial')
    });
  }
}