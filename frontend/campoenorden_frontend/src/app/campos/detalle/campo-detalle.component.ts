import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { SharedModule } from '../../shared/shared.module';
import { Labor, getTipoIcon, getEstadoColor } from '../../models/interfaces';

interface CampoDetalle {
  id: number;
  nombre: string;
  ubicacion: string;
  localidad: string;
  provincia: string;
  superficie_total: number;
  superficie_trabajada: number;
  costo_total: number;
  costo_por_ha: number;
  margen: number;
}

@Component({
  selector: 'app-campo-detalle',
  templateUrl: './campo-detalle.component.html',
  styleUrls: ['./campo-detalle.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule, SharedModule]
})
export class CampoDetalleComponent implements OnInit {
  campoId: string | null = null;
  campo: CampoDetalle | null = null;
  labores: Labor[] = [];
  loading = true;
  error: string | null = null;

  getTipoIcon = getTipoIcon;
  getEstadoColor = getEstadoColor;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  ngOnInit() {
    this.campoId = this.route.snapshot.paramMap.get('id');
    this.cargarDetalle();
  }

  cargarDetalle() {
    if (!this.campoId) return;
    this.loading = true;
    this.error = null;

    this.api.get<CampoDetalle>(`core/campos/${this.campoId}/?include_stats=true`).subscribe({
      next: (campo) => {
        if (!campo) {
          this.error = 'Campo no encontrado';
          this.loading = false;
          return;
        }
        this.campo = campo;
        this.cargarLabores();
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.loading = false;
      }
    });
  }

  cargarLabores() {
    this.api.get<Labor[]>('core/labores/', { params: { campo: this.campoId! } }).subscribe({
      next: (data) => {
        this.labores = data || [];
        this.loading = false;
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.loading = false;
      }
    });
  }

  verLabor(labor: Labor) {
    this.router.navigate(['/tabs/labores/editar', labor.id]);
  }
}
