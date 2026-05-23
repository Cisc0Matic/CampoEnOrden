import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule, ToastController, ModalController } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { TIPOS_LABOR, ESTADOS_LABOR, getEstadoColor } from '../../models/interfaces';
import { CrearPersonaModalComponent } from '../../shared/components/crear-persona-modal/crear-persona-modal.component';

@Component({
  selector: 'app-labor-form',
  templateUrl: './labor-form.component.html',
  styleUrls: ['./labor-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class LaborFormComponent implements OnInit {
  laborForm: FormGroup;
  insumosForm: FormArray;
  isEdit = false;
  laborId: string | null = null;
  loading = false;
  error: string | null = null;
  lotes: any[] = [];
  personas: any[] = [];
  insumos: any[] = [];
  tiposLaborPersonalizado: any[] = [];
  fotoPreview: string | null = null;
  fotoFile: File | null = null;

  tipos = TIPOS_LABOR;
  estados = ESTADOS_LABOR;
  getEstadoColor = getEstadoColor;

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router,
    private toastCtrl: ToastController,
    private modalCtrl: ModalController
  ) {
    this.laborForm = this.fb.group({
      lote: ['', Validators.required],
      tipo: ['SIEMBRA', Validators.required],
      sub_tipo_otra: [null],
      estado: [{ value: 'CARGADA', disabled: true }],
      fecha: ['', Validators.required],
      hectareas: [0, [Validators.required, Validators.min(0.1)]],
      precio_por_ha: [0, Validators.min(0)],
      moneda: ['USD'],
      contratista: [null],
      responsable: [null],
      costo_total: [{ value: 0, disabled: true }],
      observaciones: ['']
    });
    this.insumosForm = this.fb.array([]);
  }

  ngOnInit() {
    this.laborId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    this.cargarDatos();
    this.setupAutoCalc();
  }

  setupAutoCalc() {
    this.laborForm.get('precio_por_ha')?.valueChanges.subscribe(() => this.calcularTotal());
    this.laborForm.get('hectareas')?.valueChanges.subscribe(() => this.calcularTotal());
  }

  calcularTotal() {
    const ha = this.laborForm.get('hectareas')?.value || 0;
    const precio = this.laborForm.get('precio_por_ha')?.value || 0;
    this.laborForm.patchValue({ costo_total: ha * precio }, { emitEvent: false });
  }

  cargarPersonas() {
    this.api.get<any[]>('core/personas/').subscribe({
      next: (data) => this.personas = data || [],
      error: () => console.error('Error cargando personas')
    });
  }

  cargarDatos() {
    this.loading = true;
    this.api.get<any[]>('core/lotes/').subscribe({
      next: (lotes) => {
        this.lotes = lotes || [];
        this.cargarPersonas();
        this.api.get<any[]>('core/insumos/').subscribe({
          next: (insumos) => {
            this.insumos = insumos || [];
            this.api.get<any[]>('core/tipos-labor-personalizado/').subscribe({
              next: (tipos) => {
                this.tiposLaborPersonalizado = tipos || [];
                if (this.isEdit && this.laborId) {
                  this.cargarLabor();
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

  cargarLabor() {
    if (!this.laborId) return;
    this.api.get<any>(`core/labores/${this.laborId}/`).subscribe({
      next: (labor) => {
        this.laborForm.patchValue({
          lote: labor.lote,
          tipo: labor.tipo,
          sub_tipo_otra: labor.sub_tipo_otra,
          estado: labor.estado,
          fecha: labor.fecha,
          hectareas: labor.hectareas,
          precio_por_ha: labor.precio_por_ha,
          moneda: labor.moneda,
          contratista: labor.contratista,
          responsable: labor.responsable,
          observaciones: labor.observaciones
        });
        this.calcularTotal();

        if (labor.insumos && labor.insumos.length > 0) {
          labor.insumos.forEach((insumo: any) => {
            this.agregarInsumo(insumo);
          });
        }
        if (labor.foto_receta_url) {
          this.fotoPreview = labor.foto_receta_url;
        }
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando labor';
        this.loading = false;
      }
    });
  }

  async abrirCrearContratista() {
    await this.abrirModalPersona('CONTRATISTA', 'contratista');
  }

  async abrirCrearResponsable() {
    await this.abrirModalPersona('CONTRATISTA', 'responsable');
  }

  private async abrirModalPersona(rol: string, formControl: string) {
    const modal = await this.modalCtrl.create({
      component: CrearPersonaModalComponent,
      componentProps: { rol },
      cssClass: 'popup-modal'
    });

    await modal.present();
    const { data, role } = await modal.onWillDismiss();

    if (role === 'created' && data && data.id) {
      this.laborForm.patchValue({ [formControl]: data.id });
      this.cargarPersonas();
    }
  }

  onTipoChange(event: any) {
    const tipo = event.detail.value;
    const subTipoCtrl = this.laborForm.get('sub_tipo_otra');
    if (tipo === 'OTRA') {
      subTipoCtrl?.enable();
      subTipoCtrl?.setValidators(Validators.required);
    } else {
      subTipoCtrl?.disable();
      subTipoCtrl?.setValidators(null);
      subTipoCtrl?.setValue(null);
    }
  }

  onFotoSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.fotoFile = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        this.fotoPreview = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  removeFoto() {
    this.fotoFile = null;
    this.fotoPreview = null;
  }

  get insumosArray(): FormArray {
    return this.insumosForm;
  }

  agregarInsumo(insumo?: any) {
    const insumoGroup = this.fb.group({
      insumo: [insumo?.insumo || '', Validators.required],
      total_aplicado: [insumo?.total_aplicado || 0, Validators.min(0)],
      unidad_dosis: [insumo?.unidad_dosis || 'l/ha'],
      precio_unitario: [insumo?.precio_unitario || 0, Validators.min(0)],
      dosis_calculada: [{ value: insumo?.dosis_calculada || 0, disabled: true }],
      costo_total: [{ value: insumo?.costo_total || 0, disabled: true }]
    });
    this.insumosArray.push(insumoGroup);
    this.setupInsumoAutoCalc(insumoGroup);
  }

  setupInsumoAutoCalc(group: FormGroup) {
    group.get('total_aplicado')?.valueChanges.subscribe(() => this.calcularInsumo(group));
    group.get('precio_unitario')?.valueChanges.subscribe(() => this.calcularInsumo(group));
    group.get('insumo')?.valueChanges.subscribe(() => {
      const insumoId = group.get('insumo')?.value;
      if (insumoId) {
        this.api.get<any[]>('core/productos-precio/', { params: { insumo: insumoId } }).subscribe({
          next: (precios) => {
            if (precios && precios.length > 0) {
              const vigente = precios[0];
              group.patchValue({ precio_unitario: vigente.precio_unitario }, { emitEvent: false });
              this.calcularInsumo(group);
            }
          }
        });
      }
    });
  }

  calcularInsumo(group: FormGroup) {
    const ha = this.laborForm.get('hectareas')?.value || 1;
    const total = group.get('total_aplicado')?.value || 0;
    const precio = group.get('precio_unitario')?.value || 0;
    const dosis = ha > 0 ? total / ha : 0;
    group.patchValue({
      dosis_calculada: dosis,
      costo_total: total * precio
    }, { emitEvent: false });
  }

  eliminarInsumo(index: number) {
    this.insumosArray.removeAt(index);
  }

  guardar() {
    this.laborForm.markAllAsTouched();
    if (this.laborForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const formData = new FormData();
    const data = this.laborForm.getRawValue();
    data.insumos = this.insumosArray.value;

    if (this.fotoFile) {
      formData.append('foto_receta', this.fotoFile);
    }

    const laborData = {
      lote: data.lote,
      tipo: data.tipo,
      sub_tipo_otra: data.tipo === 'OTRA' ? data.sub_tipo_otra : null,
      estado: data.estado,
      fecha: data.fecha,
      hectareas: data.hectareas,
      precio_por_ha: data.precio_por_ha || 0,
      moneda: data.moneda,
      contratista: data.contratista,
      responsable: data.responsable,
      observaciones: data.observaciones,
      insumos: data.insumos.map((i: any) => ({
        insumo: i.insumo,
        total_aplicado: i.total_aplicado,
        unidad_dosis: i.unidad_dosis,
        precio_unitario: i.precio_unitario
      }))
    };

    formData.append('data', JSON.stringify(laborData));

    const request = this.isEdit && this.laborId
      ? this.api.put(`core/labores/${this.laborId}/`, laborData)
      : this.api.post('core/labores/', laborData);

    request.subscribe({
      next: async () => {
        const toast = await this.toastCtrl.create({
          message: 'Labor cargada correctamente',
          duration: 2000,
          color: 'success'
        });
        await toast.present();
        this.router.navigate(['/tabs/labores']);
      },
      error: async () => {
        const toast = await this.toastCtrl.create({
          message: 'Error al cargar labor',
          duration: 2000,
          color: 'danger'
        });
        await toast.present();
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }
}
