import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-documento-form',
  templateUrl: './documento-form.component.html',
  styleUrls: ['./documento-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class DocumentoFormComponent implements OnInit {
  documentoForm: FormGroup;
  isEdit = false;
  documentoId: string | null = null;
  loading = false;
  error: string | null = null;
  campos: any[] = [];
  personas: any[] = [];
  lotes: any[] = [];
  fletes: any[] = [];
  tipos = [
    { value: 'CONTRATO', label: 'Contrato' },
    { value: 'FACTURA', label: 'Factura' },
    { value: 'COMPROBANTE', label: 'Comprobante' },
    { value: 'TRANSFERENCIA', label: 'Transferencia' },
    { value: 'MAPA', label: 'Mapa' },
    { value: 'OTRO', label: 'Otro' }
  ];
  estados = [
    { value: 'PENDIENTE', label: 'Pendiente' },
    { value: 'APROBADO', label: 'Aprobado' },
    { value: 'VENCIDO', label: 'Vencido' },
    { value: 'ARCHIVADO', label: 'Archivado' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.documentoForm = this.fb.group({
      tipo: ['CONTRATO', Validators.required],
      numero: ['', Validators.required],
      campo: [null],
      labor: [null],
      flete: [null],
      titular: [null],
      monto: [0, Validators.min(0)],
      estado: ['PENDIENTE'],
      fecha_documento: ['', Validators.required],
      fecha_vencimiento: [''],
      observaciones: [''],
      archivo: [null]
    });
  }

  ngOnInit() {
    this.documentoId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.api.get<any[]>('core/campos/').subscribe({
      next: (campos) => {
        this.campos = campos || [];
        this.api.get<any[]>('core/personas/').subscribe({
          next: (personas) => {
            this.personas = personas || [];
            this.api.get<any[]>('core/lotes/').subscribe({
              next: (lotes) => {
                this.lotes = lotes || [];
                this.api.get<any[]>('core/fletes/').subscribe({
                  next: (fletes) => {
                    this.fletes = fletes || [];
                    if (this.isEdit && this.documentoId) {
                      this.cargarDocumento();
                    } else {
                      this.loading = false;
                    }
                  },
                  error: () => this.loading = false
                });
              },
              error: () => this.loading = false
            });
          },
          error: () => this.loading = false
        });
      },
      error: () => this.loading = false
    });
  }

  cargarDocumento() {
    if (!this.documentoId) return;
    this.api.get<any>(`core/documentos/${this.documentoId}/`).subscribe({
      next: (doc) => {
        this.documentoForm.patchValue({
          tipo: doc.tipo,
          numero: doc.numero,
          campo: doc.campo,
          labor: doc.labor,
          flete: doc.flete,
          titular: doc.titular,
          monto: doc.monto,
          estado: doc.estado,
          fecha_documento: doc.fecha_documento,
          fecha_vencimiento: doc.fecha_vencimiento,
          observaciones: doc.observaciones
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando documento';
        this.loading = false;
      }
    });
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.documentoForm.patchValue({ archivo: file });
    }
  }

  guardar() {
    if (this.documentoForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.documentoForm.value;
    const formData = new FormData();
    
    Object.keys(data).forEach(key => {
      if (key === 'archivo' && data[key]) {
        formData.append('archivo', data[key]);
      } else if (data[key] !== null && data[key] !== '') {
        formData.append(key, data[key].id || data[key]);
      }
    });

    const request = this.isEdit && this.documentoId
      ? this.api.put(`core/documentos/${this.documentoId}/`, formData)
      : this.api.post('core/documentos/', formData);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/documentos']),
      error: () => {
        this.error = 'Error guardando documento';
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }
}
