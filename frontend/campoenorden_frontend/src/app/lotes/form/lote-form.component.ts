import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-lote-form',
  templateUrl: './lote-form.component.html',
  styleUrls: ['./lote-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class LoteFormComponent implements OnInit {
  loteForm: FormGroup;
  isEdit = false;
  loteId: string | null = null;
  loading = false;
  error: string | null = null;
  campos: any[] = [];
  campanas: any[] = [];
  cultivos: any[] = [];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.loteForm = this.fb.group({
      campo: ['', Validators.required],
      campana: ['', Validators.required],
      cultivo: ['', Validators.required],
      superficie: [0, [Validators.required, Validators.min(0.1)]],
      rendimiento_estimado: [0, Validators.min(0)],
      precio_tn: [0, Validators.min(0)],
      tipo_cambio: [0, Validators.min(0)],
      ubicacion: [''],
      activo: [true],
      observaciones: ['']
    });
  }

  ngOnInit() {
    this.loteId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    this.cargarDatos();
  }

  cargarDatos() {
    this.loading = true;
    this.api.get<any[]>('core/campos/').subscribe({
      next: (campos) => {
        this.campos = campos || [];
        this.api.get<any[]>('core/campanas/').subscribe({
          next: (campanas) => {
            this.campanas = campanas || [];
            this.api.get<any[]>('core/cultivos/').subscribe({
              next: (cultivos) => {
                this.cultivos = cultivos || [];
                if (this.isEdit && this.loteId) {
                  this.cargarLote();
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
  }

  cargarLote() {
    if (!this.loteId) return;
    this.api.get<any>(`core/lotes/${this.loteId}/`).subscribe({
      next: (lote) => {
        this.loteForm.patchValue({
          campo: lote.campo,
          campana: lote.campana,
          cultivo: lote.cultivo,
          superficie: lote.superficie,
          rendimiento_estimado: lote.rendimiento_estimado,
          precio_tn: lote.precio_tn,
          tipo_cambio: lote.tipo_cambio,
          ubicacion: lote.ubicacion,
          activo: lote.activo,
          observaciones: lote.observaciones
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando lote';
        this.loading = false;
      }
    });
  }

  guardar() {
    if (this.loteForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.loteForm.value;
    
    const request = this.isEdit && this.loteId
      ? this.api.put(`core/lotes/${this.loteId}/`, data)
      : this.api.post('core/lotes/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/lotes']),
      error: () => {
        this.error = 'Error guardando lote';
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }
}
