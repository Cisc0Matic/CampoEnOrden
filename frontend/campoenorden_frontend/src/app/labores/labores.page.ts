import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router, RouterModule } from '@angular/router';
import { Labor, getTipoIcon, getEstadoColor } from '../models/interfaces';

@Component({
  selector: 'app-labores',
  templateUrl: './labores.page.html',
  styleUrls: ['./labores.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule]
})
export class LaboresPage implements OnInit, OnDestroy {
  labores: Labor[] = [];
  loading = true;
  error: string | null = null;
  filterTipo = '';
  private routerListener: any;

  getTipoIcon = getTipoIcon;
  getEstadoColor = getEstadoColor;

  constructor(private api: ApiService, private router: Router) {
    this.routerListener = this.router.events.subscribe(() => {
      if (this.router.url.includes('/tabs/labores')) {
        this.cargarLabores();
      }
    });
  }

  ngOnInit() {
    this.cargarLabores();
  }

  ngOnDestroy() {
    if (this.routerListener) {
      this.routerListener.unsubscribe();
    }
  }

  cargarLabores() {
    this.loading = true;
    let endpoint = 'core/labores/';
    if (this.filterTipo) {
      if (this.filterTipo === 'PULVERIZACION') {
        endpoint = 'core/labores/?tipo__in=PULVERIZACION_TERRESTRE,PULVERIZACION_DRONES,PULVERIZACION_AEREA';
      } else if (this.filterTipo === 'FERTILIZACION') {
        endpoint = 'core/labores/?tipo__in=FERTILIZACION_TERRESTRE,FERTILIZACION_DRONES';
      } else {
        endpoint = `core/labores/?tipo=${this.filterTipo}`;
      }
    }
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
    this.router.navigate(['/tabs/labores', labor.id]);
  }

  verFoto(labor: Labor) {
    if (labor.foto_receta_url) {
      window.open(labor.foto_receta_url, '_blank');
    }
  }
}
