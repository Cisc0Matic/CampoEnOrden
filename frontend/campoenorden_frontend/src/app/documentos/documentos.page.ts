import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router, ActivatedRoute } from '@angular/router';

interface Documento {
  id: number;
  tipo: string;
  tipo_display: string;
  numero: string;
  campo_nombre: string;
  campo_id: number;
  labor_id: number;
  flete_id: number;
  titular_nombre: string;
  titular_id: number;
  monto: number;
  estado: string;
  estado_display: string;
  fecha_documento: string;
  fecha_vencimiento: string;
  observaciones: string;
  archivo_url: string;
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
  documentosFiltrados: Documento[] = [];
  loading = true;
  error: string | null = null;
  filtroTipo = '';
  filtroEstado = '';
  campoId: string | null = null;

  constructor(private api: ApiService, private router: Router, private route: ActivatedRoute) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.campoId = params['campo_id'] || null;
      this.cargarDocumentos();
    });
  }

  cargarDocumentos() {
    this.loading = true;
    let endpoint = 'core/documentos/';
    const params = [];
    if (this.filtroTipo) params.push(`tipo=${this.filtroTipo}`);
    if (this.filtroEstado) params.push(`estado=${this.filtroEstado}`);
    if (this.campoId) params.push(`campo=${this.campoId}`);
    if (params.length > 0) endpoint += '?' + params.join('&');
    
    this.api.get<Documento[]>(endpoint).subscribe({
      next: (data) => {
        this.documentos = data || [];
        this.filtrarDocumentos();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar documentos';
        this.loading = false;
      }
    });
  }

  filtrarDocumentos() {
    this.documentosFiltrados = this.documentos.filter(d => {
      if (this.filtroTipo && d.tipo !== this.filtroTipo) return false;
      if (this.filtroEstado && d.estado !== this.filtroEstado) return false;
      return true;
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

  agregarDocumento() {
    this.router.navigate(['/tabs/documentos/crear']);
  }

  editarDocumento(doc: Documento) {
    this.router.navigate(['/tabs/documentos/editar', doc.id]);
  }

  verDocumento(doc: Documento) {
    if (doc.archivo_url) {
      window.open(doc.archivo_url, '_blank');
    }
  }

  cambiarEstado(doc: Documento, nuevoEstado: string) {
    this.api.put(`core/documentos/${doc.id}/`, { estado: nuevoEstado }).subscribe({
      next: () => this.cargarDocumentos(),
      error: () => console.error('Error cambiando estado')
    });
  }

  isVencido(doc: Documento): boolean {
    if (!doc.fecha_vencimiento) return false;
    return new Date(doc.fecha_vencimiento) < new Date();
  }
}