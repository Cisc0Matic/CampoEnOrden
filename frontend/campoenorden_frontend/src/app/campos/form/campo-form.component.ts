import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule, ToastController, ModalController } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { CrearPersonaModalComponent } from '../../shared/components/crear-persona-modal/crear-persona-modal.component';

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
  provincias: any[] = [];
  estados = [
    { value: 'ACTIVO', label: 'Activo' },
    { value: 'PENDIENTE', label: 'Pendiente' },
    { value: 'VENCIDO', label: 'Vencido' },
    { value: 'RENOVADO', label: 'Renovado' }
  ];
  private provinciasFallback = [
    'Buenos Aires', 'Catamarca', 'Chaco', 'Chubut', 'Ciudad Autónoma de Buenos Aires',
    'Córdoba', 'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
    'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis',
    'Santa Cruz', 'Santa Fe', 'Santiago del Estero', 'Tierra del Fuego', 'Tucumán'
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router,
    private toastCtrl: ToastController,
    private modalCtrl: ModalController
  ) {
    this.campoForm = this.fb.group({
      nombre: ['', Validators.required],
      ubicacion: [''],
      localidad: [''],
      provincia: [''],
      productor: [null],
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
    this.cargarProvincias();
    
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

  cargarProvincias() {
    this.api.get<any[]>('core/provincias/').subscribe({
      next: (data) => {
        this.provincias = data || [];
      },
      error: () => {
        this.provincias = this.provinciasFallback.map(n => ({ codigo: '', nombre: n }));
      }
    });
  }

  async abrirCrearLocador() {
    await this.abrirModalPersona('DUENO', 'locadores_ids');
  }

  async abrirCrearLocatario() {
    await this.abrirModalPersona('ARRENDATARIO', 'locatarios_ids');
  }

  private async abrirModalPersona(rol: string, formControl: string) {
    const modal = await this.modalCtrl.create({
      component: CrearPersonaModalComponent,
      componentProps: { rol },
      breakpoints: [0, 0.75, 1],
      initialBreakpoint: 0.75
    });

    await modal.present();
    const { data } = await modal.onWillDismiss();

    if (data && data.id) {
      const currentIds = this.campoForm.get(formControl)?.value || [];
      this.campoForm.patchValue({
        [formControl]: [...currentIds, data.id]
      });
      this.cargarPersonas();
    }
  }

  cargarCampo() {
    if (!this.campoId) return;
    this.loading = true;
    this.api.get<any>(`core/campos/${this.campoId}/`).subscribe({
      next: (campo) => {
        this.campoForm.patchValue({
          nombre: campo.nombre,
          ubicacion: campo.ubicacion,
          localidad: campo.localidad,
          provincia: campo.provincia,
          productor: campo.productor,
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
      next: async () => {
        const toast = await this.toastCtrl.create({
          message: 'Campo cargado correctamente',
          duration: 2000,
          color: 'success'
        });
        await toast.present();
        this.router.navigate(['/tabs/campos']);
      },
      error: async () => {
        const toast = await this.toastCtrl.create({
          message: 'Error al cargar campo',
          duration: 2000,
          color: 'danger'
        });
        await toast.present();
        this.loading = false;
      }
    });
  }

}
