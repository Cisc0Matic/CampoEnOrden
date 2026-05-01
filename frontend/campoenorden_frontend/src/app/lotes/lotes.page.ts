import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router, RouterModule } from '@angular/router';

interface Lote {
  id: number;
  nombre: string;
  campo_nombre: string;
  campo_id: number;
  campana_nombre: string;
  campana_id: number;
  cultivo_nombre: string;
  cultivo_id: number;
  superficie: number;
  rendimiento_estimado: number;
  precio_tn: number;
  tipo_cambio: number;
  ubicacion: string;
  activo: boolean;
  observaciones: string;
}

interface Campana {
  id: number;
  nombre: string;
}

interface Cultivo {
  id: number;
  nombre: string;
}

@Component({
  selector: 'app-lotes',
  templateUrl: './lotes.page.html',
  styleUrls: ['./lotes.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule]
})
export class LotesPage implements OnInit {
  lotes: Lote[] = [];
  lotesFiltrados: Lote[] = [];
  campanas: Campana[] = [];
  cultivos: Cultivo[] = [];
  loading = true;
  error: string | null = null;
  filtroTipo = '';
  filtroCampana = '';
  filtroCultivo = '';
  filtroActivo: any = 'todos';

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.api.get<Campana[]>('core/campanas/').subscribe({
      next: (campanas) => {
        this.campanas = campanas || [];
        this.api.get<Cultivo[]>('core/cultivos/').subscribe({
          next: (cultivos) => {
            this.cultivos = cultivos || [];
            this.cargarLotes();
          },
          error: () => this.cargarLotes()
        });
      },
      error: () => this.cargarLotes()
    });
  }

  cargarLotes() {
    this.api.get<Lote[]>('core/lotes/').subscribe({
      next: (data) => {
        this.lotes = data || [];
        this.filtrarLotes();
        this.loading = false;
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.lotes = [];
        this.loading = false;
      }
    });
  }

  filtrarLotes() {
    this.lotesFiltrados = this.lotes.filter(l => {
      if (this.filtroCampana && l.campana_id?.toString() !== this.filtroCampana) return false;
      if (this.filtroCultivo && l.cultivo_id?.toString() !== this.filtroCultivo) return false;
      if (this.filtroActivo === 'activos') return l.activo;
      if (this.filtroActivo === 'inactivos') return !l.activo;
      return true;
    });
  }

  filtrarPorTipo(tipo: string) {
    this.filtroTipo = this.filtroTipo === tipo ? '' : tipo;
    this.filtrarLotes();
  }

  getCultivoIcon(cultivo: string): string {
    if (!cultivo) return 'help-circle';
    const lower = cultivo.toLowerCase();
    if (lower.includes('trigo') || lower.includes('trigo')) return 'nutrition';
    if (lower.includes('soja')) return 'leaf';
    if (lower.includes('maiz') || lower.includes('maíz')) return 'rose';
    if (lower.includes('cebada') || lower.includes('avena')) return 'grass';
    return 'grid';
  }

  agregarLote() {
    this.router.navigate(['/tabs/lotes/crear']);
  }

  editarLote(lote: Lote) {
    this.router.navigate(['/tabs/lotes/editar', lote.id]);
  }

  verDetalleLote(lote: Lote) {
    this.router.navigate(['/tabs/lotes', lote.id]);
  }
}
