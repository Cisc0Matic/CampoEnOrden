import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Lote {
  id: number;
  nombre: string;
  campo_nombre: string;
  campana_nombre: string;
  cultivo_nombre: string;
  superficie: number;
  rendimiento_estimado: number;
  precio_tn: number;
  tipo_cambio: number;
  ubicacion: string;
  activo: boolean;
  observaciones: string;
}

@Component({
  selector: 'app-lotes',
  templateUrl: './lotes.page.html',
  styleUrls: ['./lotes.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class LotesPage implements OnInit {
  lotes: Lote[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarLotes();
  }

  cargarLotes() {
    this.loading = true;
    this.api.get<Lote[]>('core/lotes/').subscribe({
      next: (data) => {
        this.lotes = data || [];
        this.loading = false;
      },
      error: () => {
        this.error = 'Backend no disponible';
        this.lotes = [];
        this.loading = false;
      }
    });
  }

  getCultivoIcon(cultivo: string): string {
    if (!cultivo) return 'help-circle';
    const lower = cultivo.toLowerCase();
    if (lower.includes('trigo') || lower.includes(' trigo')) return 'nutrition';
    if (lower.includes('soja')) return 'leaf';
    if (lower.includes('maíz') || lower.includes('maiz')) return 'rose';
    if (lower.includes('cebada') || lower.includes('avena')) return 'grass';
    return 'grid';
  }
}