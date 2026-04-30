import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';

interface DashboardData {
  campos_activos: number;
  hectareas_totales: number;
  hectareas_trabajadas: number;
  labores_cargadas: number;
  costos_totales: number;
  costos_por_ha: number;
  documentos_pendientes: number;
  alertas: string[];
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class DashboardComponent implements OnInit {
  datos: DashboardData | null = null;
  loading = true;
  error: string | null = null;

  constructor(
    private api: ApiService,
    private storage: Storage,
    private router: Router
  ) {}

  ngOnInit() {
    this.cargarDashboard();
  }

cargarDashboard() {
    this.loading = true;
    this.error = null;
    
    this.api.get<DashboardData>('core/dashboard/').subscribe({
      next: (data) => {
        this.datos = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error cargando dashboard:', err);
        if (err.status === 401) {
          this.cerrarSesion();
          return;
        }
        this.datos = null;
        this.loading = false;
      }
    });
  }

  getAlertClass(alerta: string): string {
    const lower = alerta.toLowerCase();
    if (lower.includes('vencido')) return 'alert-danger';
    if (lower.includes('pendiente')) return 'alert-warning';
    return 'alert-info';
  }

  getAlertIcon(alerta: string): string {
    const lower = alerta.toLowerCase();
    if (lower.includes('vencido')) return 'warning';
    if (lower.includes('pendiente')) return 'time';
    return 'information-circle';
  }

  getProgressWidth(): number {
    if (!this.datos?.hectareas_totales) return 0;
    return (this.datos.hectareas_trabajadas / this.datos.hectareas_totales) * 100;
  }

  async cerrarSesion() {
    await this.storage.remove('jwt_token');
    await this.storage.remove('username');
    window.location.href = '/login';
  }
}