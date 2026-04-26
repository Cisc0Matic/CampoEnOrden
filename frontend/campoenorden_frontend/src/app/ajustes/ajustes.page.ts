import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Parametro {
  id: number;
  nombre: string;
  categoria: string;
  categoria_display: string;
  valor: number;
  unidad: string;
  campana_nombre: string;
  vigente: boolean;
}

@Component({
  selector: 'app-ajustes',
  templateUrl: './ajustes.page.html',
  styleUrls: ['./ajustes.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class AjustesPage implements OnInit {
  parametros: Parametro[] = [];
  loading = true;
  error: string | null = null;
  categorias: string[] = ['GRANO', 'INSUMO', 'LABOR', 'COMERCIALIZACION', 'COSECHA', 'TIPO_CAMBIO', 'UNIDAD'];
  categoriaSeleccionada: string = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarParametros();
  }

  cargarParametros() {
    this.loading = true;
    let path = 'core/parametros/';
    if (this.categoriaSeleccionada) {
      path += `?categoria=${this.categoriaSeleccionada}`;
    }
    this.api.get<Parametro[]>(path).subscribe({
      next: (data) => {
        this.parametros = data || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar parámetros';
        this.loading = false;
      }
    });
  }

  filtrarPorCategoria(cat: string) {
    this.categoriaSeleccionada = cat;
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
}