import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router, RouterModule } from '@angular/router';

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
  margen: number;
  condiciones_alquiler: string;
  observaciones: string;
  alquiler_pendiente: number;
  documentos_count?: number;
  locadores_nombres?: string;
  locatarios_nombres?: string;
}

@Component({
  selector: 'app-campos',
  templateUrl: './campos.page.html',
  styleUrls: ['./campos.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule]
})
export class CamposPage implements OnInit {
  campos: Campo[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.cargarCampos();
  }

  cargarCampos() {
    this.loading = true;
    this.api.get<any>('core/campos/?include_stats=true').subscribe({
      next: (data) => {
        this.campos = (data || []).map((c: any) => ({
          ...c,
          margen: c.margen || 0,
          documentos_count: c.documentos_count || 0,
          locadores_nombres: c.locadores_nombres || '',
          locatarios_nombres: c.locatarios_nombres || ''
        }));
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

  agregarCampo() {
    this.router.navigate(['/tabs/campos/crear']);
  }

  editarCampo(campo: Campo) {
    this.router.navigate(['/tabs/campos/editar', campo.id]);
  }

  verDocumentos(campo: Campo) {
    this.router.navigate(['/documentos'], { queryParams: { campo_id: campo.id } });
  }
}