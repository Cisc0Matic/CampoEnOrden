import { Component, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Storage } from '@ionic/storage-angular';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MargenData, MargenConcepto } from '../models/interfaces';

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
  imports: [CommonModule, IonicModule, RouterModule, FormsModule],
  providers: [DecimalPipe]
})
export class DashboardComponent implements OnInit {
  datos: DashboardData | null = null;
  margen: MargenData | null = null;
  loading = true;
  error: string | null = null;
  campos: any[] = [];
  campoFiltro: number | null = null;

  svgSize = 220;
  centerX = 110;
  centerY = 110;
  radius = 90;

  private readonly COLORS = [
    '#4CAF50', '#2196F3', '#FF9800', '#9C27B0',
    '#F44336', '#00BCD4', '#795548', '#607D8B'
  ];

  constructor(
    private api: ApiService,
    private storage: Storage,
    private router: Router,
    private decimalPipe: DecimalPipe
  ) {}

  ngOnInit() {
    this.cargarDashboard();
    this.cargarCampos();
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
        if (err.status === 401) {
          this.cerrarSesion();
          return;
        }
        this.datos = null;
        this.loading = false;
      }
    });
  }

  cargarCampos() {
    this.api.get<any[]>('core/campos/').subscribe({
      next: (data) => this.campos = data || []
    });
  }

  cargarMargen() {
    let endpoint = 'core/dashboard/margen/';
    if (this.campoFiltro) {
      endpoint += `?campo=${this.campoFiltro}`;
    }
    this.api.get<MargenData>(endpoint).subscribe({
      next: (data) => this.margen = data
    });
  }

  filtrarPorCampo() {
    this.cargarMargen();
  }

  getDonutSegments(): { path: string; color: string; label: string; percent: number; value: number }[] {
    if (!this.margen?.conceptos) return [];
    const total = this.margen.total_costos_variables;
    if (!total) return [];

    let currentAngle = -Math.PI / 2;
    return this.margen.conceptos
      .filter(c => c.usd_total > 0)
      .map((c, i) => {
        const percent = c.usd_total / total;
        const angle = percent * 2 * Math.PI;
        const startAngle = currentAngle;
        const endAngle = currentAngle + angle;
        currentAngle = endAngle;
        return {
          path: this.describeArc(this.centerX, this.centerY, this.radius, startAngle, endAngle),
          color: this.COLORS[i % this.COLORS.length],
          label: c.concepto,
          percent: Math.round(percent * 1000) / 10,
          value: c.usd_total
        };
      });
  }

  get totalCostsDisplay(): string {
    if (!this.margen) return '$0';
    return this.decimalPipe.transform(this.margen.total_costos_variables, '1.0-0') || '$0';
  }

  get margenBrutoDisplay(): string {
    if (!this.margen) return '$0';
    return this.decimalPipe.transform(this.margen.margen_bruto, '1.0-0') || '$0';
  }

  get roiDisplay(): string {
    if (!this.margen) return '0%';
    return `${this.margen.rentabilidad_roi.toFixed(1)}%`;
  }

  getColor(index: number): string {
    return this.COLORS[index % this.COLORS.length];
  }

  getBarWidth(usdTotal: number): number {
    if (!this.margen?.total_costos_variables) return 0;
    return (usdTotal / this.margen.total_costos_variables) * 100;
  }

  private polarToCartesian(cx: number, cy: number, r: number, angle: number) {
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle)
    };
  }

  private describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number): string {
    const start = this.polarToCartesian(cx, cy, r, endAngle);
    const end = this.polarToCartesian(cx, cy, r, startAngle);
    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0;

    return [
      `M ${cx} ${cy}`,
      `L ${start.x} ${start.y}`,
      `A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
      'Z'
    ].join(' ');
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
