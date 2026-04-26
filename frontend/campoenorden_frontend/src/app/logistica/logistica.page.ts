import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Flete {
  id: number;
  nro_cpe: string;
  ctg: string;
  chofer_nombre: string;
  patente_camion: string;
  patente_acoplado: string;
  peso_origen: number;
  peso_destino: number;
  estado: string;
  estado_display: string;
  flete_corto: number;
  flete_largo: number;
  comision: number;
  secada: number;
  cosecha: number;
  destino: string;
}

@Component({
  selector: 'app-logistica',
  templateUrl: './logistica.page.html',
  styleUrls: ['./logistica.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class LogisticaPage implements OnInit {
  fletes: Flete[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarFletes();
  }

  cargarFletes() {
    this.loading = true;
    this.api.get<Flete[]>('core/fletes/').subscribe({
      next: (data) => {
        this.fletes = data || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Backend no disponible';
        this.fletes = [];
        this.loading = false;
      }
    });
  }

  getEstadoColor(estado: string): string {
    switch (estado) {
      case 'ENTREGADO': return 'success';
      case 'EN_TRASLADO': return 'warning';
      case 'FACTURADO': return 'primary';
      default: return 'medium';
    }
  }

  getCostoTotal(flete: Flete): number {
    return (flete.flete_corto || 0) + (flete.flete_largo || 0) + (flete.comision || 0) + (flete.secada || 0) + (flete.cosecha || 0);
  }
}