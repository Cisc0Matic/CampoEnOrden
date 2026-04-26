import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Documento {
  id: number;
  tipo: string;
  tipo_display: string;
  numero: string;
  campo_nombre: string;
  titular_nombre: string;
  monto: number;
  estado: string;
  estado_display: string;
  fecha_documento: string;
  observaciones: string;
}

@Component({
  selector: 'app-documentos',
  templateUrl: './documentos.page.html',
  styleUrls: ['./documentos.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class DocumentosPage implements OnInit {
  documentos: Documento[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarDocumentos();
  }

  cargarDocumentos() {
    this.loading = true;
    this.api.get<Documento[]>('core/documentos/').subscribe({
      next: (data) => {
        this.documentos = data || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar documentos';
        this.loading = false;
      }
    });
  }

  getEstadoColor(estado: string): string {
    switch (estado) {
      case 'APROBADO': return 'success';
      case 'PENDIENTE': return 'warning';
      case 'VENCIDO': return 'danger';
      case 'ARCHIVADO': return 'medium';
      default: return 'medium';
    }
  }

  getTipoIcon(tipo: string): string {
    switch (tipo) {
      case 'CONTRATO': return 'document-lock';
      case 'FACTURA': return 'receipt';
      case 'COMPROBANTE': return 'cash';
      case 'TRANSFERENCIA': return 'swap-horizontal';
      case 'MAPA': return 'map';
      default: return 'document';
    }
  }
}