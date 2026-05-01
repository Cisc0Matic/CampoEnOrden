import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-flete-form',
  templateUrl: './flete-form.component.html',
  styleUrls: ['./flete-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class FleteFormComponent implements OnInit {
  fleteForm: FormGroup;
  isEdit = false;
  fleteId: string | null = null;
  loading = false;
  error: string | null = null;
  lotes: any[] = [];
  personas: any[] = [];
  estados = [
    { value: 'PENDIENTE', label: 'Pendiente' },
    { value: 'EN_TRASLADO', label: 'En Traslado' },
    { value: 'ENTREGADO', label: 'Entregado' },
    { value: 'FACTURADO', label: 'Facturado' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.fleteForm = this.fb.group({
      nro_cpe: ['', Validators.required],
      ctg: [''],
      lote: ['', Validators.required],
      chofer: [null],
      patente_camion: ['', Validators.required],
      patente_acoplado: [''],
      fecha_hora_salida: [''],
      fecha_hora_llegada: [''],
      peso_origen: [0, Validators.min(0)],
      peso_destino: [0, Validators.min(0)],
      flete_corto: [0, Validators.min(0)],
      flete_largo: [0, Validators.min(0)],
      comision: [0, Validators.min(0)],
      secada: [0, Validators.min(0)],
      cosecha: [0, Validators.min(0)],
      costo_comercial: [0, Validators.min(0)],
      destino: [''],
      observaciones: [''],
      estado: ['PENDIENTE']
    });
  }

  ngOnInit() {
    this.fleteId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.api.get<any[]>('core/lotes/').subscribe({
      next: (lotes) => {
        this.lotes = lotes || [];
        this.api.get<any[]>('core/personas/').subscribe({
          next: (personas) => {
            this.personas = personas || [];
            if (this.isEdit && this.fleteId) {
              this.cargarFlete();
            } else {
              this.loading = false;
            }
          },
          error: () => this.loading = false
        });
      },
      error: () => this.loading = false
    });
  }

  cargarFlete() {
    if (!this.fleteId) return;
    this.api.get<any>(`core/fletes/${this.fleteId}/`).subscribe({
      next: (flete) => {
        this.fleteForm.patchValue({
          nro_cpe: flete.nro_cpe,
          ctg: flete.ctg,
          lote: flete.lote,
          chofer: flete.chofer,
          patente_camion: flete.patente_camion,
          patente_acoplado: flete.patente_acoplado,
          fecha_hora_salida: flete.fecha_hora_salida,
          fecha_hora_llegada: flete.fecha_hora_llegada,
          peso_origen: flete.peso_origen,
          peso_destino: flete.peso_destino,
          flete_corto: flete.flete_corto,
          flete_largo: flete.flete_largo,
          comision: flete.comision,
          secada: flete.secada,
          cosecha: flete.cosecha,
          costo_comercial: flete.costo_comercial,
          destino: flete.destino,
          observaciones: flete.observaciones,
          estado: flete.estado
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando flete';
        this.loading = false;
      }
    });
  }

  guardar() {
    if (this.fleteForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.fleteForm.value;
    
    const request = this.isEdit && this.fleteId
      ? this.api.put(`core/fletes/${this.fleteId}/`, data)
      : this.api.post('core/fletes/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/logistica']),
      error: () => {
        this.error = 'Error guardando flete';
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }

  getCostoTotal(): number {
    const v = this.fleteForm.value;
    return (v.flete_corto || 0) + (v.flete_largo || 0) + (v.comision || 0) + 
           (v.secada || 0) + (v.cosecha || 0) + (v.costo_comercial || 0);
  }
}
