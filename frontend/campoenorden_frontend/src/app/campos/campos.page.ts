import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Campo {
  id: number;
  nombre: string;
  ubicacion: string;
  superficie_total: number;
  superficie_trabajada: number;
  estado_contrato: string;
  estado_contrato_display: string;
  costo_total: number;
  costo_por_ha: number;
  condiciones_alquiler: string;
  observaciones: string;
  alquiler_pendiente: number;
}

@Component({
  selector: 'app-campos',
  templateUrl: './campos.page.html',
  styleUrls: ['./campos.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class CamposPage implements OnInit {
  campos: Campo[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarCampos();
  }

  cargarCampos() {
    this.loading = true;
    this.api.get<Campo[]>('core/campos/').subscribe({
      next: (data) => {
        this.campos = data || [];
        this.loading = false;
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.campos = [];
        this.loading = false;
      }
    });
  }

  getEstadoColor(estado: string): string {
    switch (estado) {
      case 'ACTIVO': return 'success';
      case 'VENCIDO': return 'danger';
      case 'PENDIENTE': return 'warning';
      case 'RENOVADO': return 'primary';
      default: return 'medium';
    }
  }

  hasAlquiler(campo: Campo): boolean {
    return campo.alquiler_pendiente > 0;
  }

  hasObservaciones(campo: Campo): boolean {
    return !!campo.observaciones;
  }
}