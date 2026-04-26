import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Labor {
  id: number;
  tipo: string;
  tipo_display: string;
  fecha: string;
  lote_nombre: string;
  campo_nombre: string;
  hectareas: number;
  costo_total: number;
  costo_dolares_ha: number;
  costo_pesos_ha: number;
  contratista_nombre: string;
  qq_ha: number;
  observaciones: string;
  insumos: any[];
}

@Component({
  selector: 'app-labores',
  templateUrl: './labores.page.html',
  styleUrls: ['./labores.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class LaboresPage implements OnInit {
  labores: Labor[] = [];
  loading = true;
  error: string | null = null;
  filterTipo = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarLabores();
  }

  cargarLabores() {
    this.loading = true;
    const endpoint = this.filterTipo ? `core/labores/?tipo=${this.filterTipo}` : 'core/labores/';
    this.api.get<Labor[]>(endpoint).subscribe({
      next: (data) => {
        this.labores = data || [];
        this.loading = false;
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.labores = [];
        this.loading = false;
      }
    });
  }

  filtrarPorTipo(tipo: string) {
    this.filterTipo = tipo;
    this.cargarLabores();
  }

  getTipoIcon(tipo: string): string {
    switch (tipo) {
      case 'PULVERIZACION': return 'water';
      case 'SIEMBRA': return 'leaf';
      case 'FERTILIZACION': return 'flask';
      case 'COSECHA': return 'grid';
      default: return 'construct';
    }
  }

  getTipoColor(tipo: string): string {
    switch (tipo) {
      case 'PULVERIZACION': return 'primary';
      case 'SIEMBRA': return 'success';
      case 'FERTILIZACION': return 'warning';
      case 'COSECHA': return 'tertiary';
      default: return 'medium';
    }
  }

  hasInsumos(labor: Labor): boolean {
    return labor.insumos && labor.insumos.length > 0;
  }
}