import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { HttpParams } from '@angular/common/http';
import { ApiService } from '../services/api.service';
import { Router, RouterModule } from '@angular/router';
import { Labor, getTipoIcon, getEstadoColor, getHeaderClass } from '../models/interfaces';

@Component({
  selector: 'app-labores',
  templateUrl: './labores.page.html',
  styleUrls: ['./labores.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule]
})
export class LaboresPage {
  labores: Labor[] = [];
  loading = true;
  error: string | null = null;
  filterTipo = '';

  getTipoIcon = getTipoIcon;
  getEstadoColor = getEstadoColor;
  getHeaderClass = getHeaderClass;

  constructor(private api: ApiService, private router: Router) {}

  ionViewWillEnter() {
    this.cargarLabores();
  }

  cargarLabores() {
    this.loading = true;
    let params = new HttpParams();
    if (this.filterTipo) {
      if (this.filterTipo === 'PULVERIZACION') {
        params = params.set('tipo__in', 'PULVERIZACION_TERRESTRE,PULVERIZACION_DRONES,PULVERIZACION_AEREA');
      } else if (this.filterTipo === 'FERTILIZACION') {
        params = params.set('tipo__in', 'FERTILIZACION_TERRESTRE,FERTILIZACION_DRONES');
      } else {
        params = params.set('tipo', this.filterTipo);
      }
    }
    this.api.get<Labor[]>('core/labores/', { params }).subscribe({
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
    this.filterTipo = this.filterTipo === tipo ? '' : tipo;
    this.cargarLabores();
  }

  hasInsumos(labor: Labor): boolean {
    return labor.insumos && labor.insumos.length > 0;
  }

  agregarLabor() {
    this.router.navigate(['/tabs/labores/crear']);
  }

  editarLabor(labor: Labor) {
    this.router.navigate(['/tabs/labores/editar', labor.id]);
  }

  verDetalleLabor(labor: Labor) {
    this.router.navigate(['/tabs/labores/editar', labor.id]);
  }

  verFoto(labor: Labor) {
    if (labor.foto_receta_url) {
      window.open(labor.foto_receta_url, '_blank');
    }
  }
}
