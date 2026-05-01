import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-campo-form',
  templateUrl: './campo-form.component.html',
  styleUrls: ['./campo-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class CampoFormComponent implements OnInit {
  campoForm: FormGroup;
  isEdit = false;
  campoId: string | null = null;
  loading = false;
  error: string | null = null;
  personas: any[] = [];
  estados = [
    { value: 'ACTIVO', label: 'Activo' },
    { value: 'PENDIENTE', label: 'Pendiente' },
    { value: 'VENCIDO', label: 'Vencido' },
    { value: 'RENOVADO', label: 'Renovado' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.campoForm = this.fb.group({
      nombre: ['', Validators.required],
      ubicacion: [''],
      superficie_total: [0, [Validators.required, Validators.min(0)]],
      superficie_trabajada: [0, Validators.min(0)],
      estado_contrato: ['ACTIVO'],
      condiciones_alquiler: [''],
      observaciones: [''],
      costo_total: [0],
      costo_por_ha: [0],
      margen: [0],
      alquiler_pendiente: [0],
      locadores_ids: [[]],
      locatarios_ids: [[]]
    });
  }

  ngOnInit() {
    this.campoId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    this.cargarPersonas();
    
    if (this.isEdit && this.campoId) {
      this.cargarCampo();
    }
  }

  cargarPersonas() {
    this.api.get<any[]>('core/personas/').subscribe({
      next: (data) => this.personas = data || [],
      error: () => console.error('Error cargando personas')
    });
  }

  cargarCampo() {
    if (!this.campoId) return;
    this.loading = true;
    this.api.get<any>(`core/campos/${this.campoId}/`).subscribe({
      next: (campo) => {
        this.campoForm.patchValue({
          nombre: campo.nombre,
          ubicacion: campo.ubicacion,
          superficie_total: campo.superficie_total,
          superficie_trabajada: campo.superficie_trabajada,
          estado_contrato: campo.estado_contrato,
          condiciones_alquiler: campo.condiciones_alquiler,
          observaciones: campo.observaciones,
          costo_total: campo.costo_total,
          costo_por_ha: campo.costo_por_ha,
          margen: campo.margen,
          alquiler_pendiente: campo.alquiler_pendiente,
          locadores_ids: campo.locadores || [],
          locatarios_ids: campo.locatarios || []
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando campo';
        this.loading = false;
      }
    });
  }

  guardar() {
    if (this.campoForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.campoForm.value;
    
    const request = this.isEdit && this.campoId
      ? this.api.put(`core/campos/${this.campoId}/`, data)
      : this.api.post('core/campos/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/campos']),
      error: () => {
        this.error = 'Error guardando campo';
        this.loading = false;
      }
    });
  }

  compararPersona(p1: any, p2: any): boolean {
    return p1 && p2 ? p1.id === p2.id : p1 === p2;
  }
}
