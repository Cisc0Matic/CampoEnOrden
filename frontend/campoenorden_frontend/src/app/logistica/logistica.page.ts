import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';

interface Flete {
  id: number;
  nro_cpe: string;
  ctg: string;
  chofer_nombre: string;
  chofer_id: number;
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
  costo_comercial: number;
  destino: string;
  lote_info: string;
  campo_nombre: string;
  fecha_hora_salida: string;
  fecha_hora_llegada: string;
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
  filtroEstado = '';

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.cargarFletes();
  }

  cargarFletes() {
    this.loading = true;
    const endpoint = this.filtroEstado ? `core/fletes/?estado=${this.filtroEstado}` : 'core/fletes/';
    this.api.get<Flete[]>(endpoint).subscribe({
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

  filtrarPorEstado(estado: string) {
    this.filtroEstado = estado;
    this.cargarFletes();
  }

  getEstadoColor(estado: string): string {
    switch (estado) {
      case 'ENTREGADO': return 'success';
      case 'EN_TRASLADO': return 'warning';
      case 'FACTURADO': return 'primary';
      case 'PENDIENTE': return 'medium';
      default: return 'medium';
    }
  }

  getCostoTotal(flete: Flete): number {
    return (flete.flete_corto || 0) + (flete.flete_largo || 0) + 
           (flete.comision || 0) + (flete.secada || 0) + 
           (flete.cosecha || 0) + (flete.costo_comercial || 0);
  }

  agregarFlete() {
    this.router.navigate(['/tabs/logistica/crear']);
  }

  editarFlete(flete: Flete) {
    this.router.navigate(['/tabs/logistica/editar', flete.id]);
  }

  verCPE(flete: Flete) {
    this.router.navigate(['/tabs/logistica', flete.id, 'cpe']);
  }

  actualizarEstado(flete: Flete, nuevoEstado: string) {
    this.api.put(`core/fletes/${flete.id}/`, { estado: nuevoEstado }).subscribe({
      next: () => this.cargarFletes(),
      error: () => console.error('Error actualizando estado')
    });
  }
}