import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

interface Lote {
  id: number;
  nombre: string;
  campo: number;
  campo_nombre: string;
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
export class LotesPage implements OnInit, OnDestroy {
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
  filtroCampo: number | null = null;
  pageTitle = 'Lotes';
  private routerListener: any;

  constructor(private api: ApiService, private router: Router, private route: ActivatedRoute) {
    this.routerListener = this.router.events.subscribe(() => {
      if (this.router.url.includes('/tabs/lotes')) {
        this.cargarDatos();
      }
    });
  }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      const campoId = params['campo_id'];
      if (campoId) {
        this.filtroCampo = Number(campoId);
        this.pageTitle = `Lotes de ${params['campo_nombre'] || 'Campo'}`;
      }
    });
    this.cargarDatos();
  }

  ngOnDestroy() {
    if (this.routerListener) {
      this.routerListener.unsubscribe();
    }
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
      if (this.filtroCampo !== null && l.campo !== this.filtroCampo) return false;
      if (this.filtroCampana && l.campana_id?.toString() !== this.filtroCampana) return false;
      if (this.filtroCultivo && l.cultivo_id?.toString() !== this.filtroCultivo) return false;
      if (this.filtroActivo === 'activos') return l.activo;
      if (this.filtroActivo === 'inactivos') return !l.activo;
      return true;
    });
  }

  filtrarPorActivo(activo: string) {
    this.filtroActivo = this.filtroActivo === activo ? 'todos' : activo;
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
    const queryParams: any = {};
    if (this.filtroCampo !== null) {
      queryParams.campo_id = this.filtroCampo;
    }
    this.router.navigate(['/tabs/lotes/crear'], { queryParams });
  }

  editarLote(lote: Lote) {
    this.router.navigate(['/tabs/lotes/editar', lote.id]);
  }

  verDetalleLote(lote: Lote) {
    this.router.navigate(['/tabs/lotes/editar', lote.id]);
  }
}
