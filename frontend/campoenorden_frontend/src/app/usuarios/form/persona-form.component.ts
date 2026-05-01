import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-persona-form',
  templateUrl: './persona-form.component.html',
  styleUrls: ['./persona-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class PersonaFormComponent implements OnInit {
  personaForm: FormGroup;
  isEdit = false;
  personaId: string | null = null;
  loading = false;
  error: string | null = null;
  tipos = [
    { value: 'PERSONA', label: 'Persona' },
    { value: 'EMPRESA', label: 'Empresa' }
  ];
  roles = [
    { value: 'DUENO', label: 'Dueño' },
    { value: 'ARRENDATARIO', label: 'Arrendatario' },
    { value: 'CONTRATISTA', label: 'Contratista' },
    { value: 'CHOFER', label: 'Chofer' },
    { value: 'BENEFICIARIO', label: 'Beneficiario' },
    { value: 'ADMINISTRADOR', label: 'Administrador' },
    { value: 'RESPONSABLE_CARGA', label: 'Responsable de Carga' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.personaForm = this.fb.group({
      nombre: ['', Validators.required],
      tipo: ['PERSONA', Validators.required],
      rol: ['', Validators.required],
      documento: [''],
      cuil: [''],
      direccion: [''],
      telefono: [''],
      email: ['', Validators.email],
      activo: [true]
    });
  }

  ngOnInit() {
    this.personaId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    if (this.isEdit && this.personaId) {
      this.cargarPersona();
    }
  }

  cargarPersona() {
    if (!this.personaId) return;
    this.loading = true;
    this.api.get<any>(`core/personas/${this.personaId}/`).subscribe({
      next: (persona) => {
        this.personaForm.patchValue({
          nombre: persona.nombre,
          tipo: persona.tipo,
          rol: persona.rol,
          documento: persona.documento,
          cuil: persona.cuil,
          direccion: persona.direccion,
          telefono: persona.telefono,
          email: persona.email,
          activo: persona.activo
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando persona';
        this.loading = false;
      }
    });
  }

  guardar() {
    if (this.personaForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.personaForm.value;
    
    const request = this.isEdit && this.personaId
      ? this.api.put(`core/personas/${this.personaId}/`, data)
      : this.api.post('core/personas/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/usuarios']),
      error: () => {
        this.error = 'Error guardando persona';
        this.loading = false;
      }
    });
  }
}
