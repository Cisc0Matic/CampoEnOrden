import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

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
  tipos = [
    { value: 'PULVERIZACION', label: 'Pulverización' },
    { value: 'SIEMBRA', label: 'Siembra' },
    { value: 'FERTILIZACION', label: 'Fertilización' },
    { value: 'COSECHA', label: 'Cosecha' },
    { value: 'OTRA', label: 'Otra' }
  ];
  insumos: any[] = [];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.laborForm = this.fb.group({
      lote: ['', Validators.required],
      tipo: ['PULVERIZACION', Validators.required],
      fecha: ['', Validators.required],
      contratista: [null],
      hectareas: [0, [Validators.required, Validators.min(0.1)]],
      costo_total: [0, Validators.min(0)],
      costo_dolares_ha: [0, Validators.min(0)],
      costo_pesos_ha: [0, Validators.min(0)],
      qq_ha: [0, Validators.min(0)],
      observaciones: ['']
    });
    this.insumosForm = this.fb.array([]);
  }

  ngOnInit() {
    this.laborId = this.route.snapshot.paramMap.get('id');
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
            this.api.get<any[]>('core/insumos/').subscribe({
              next: (insumos) => {
                this.insumos = insumos || [];
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
          fecha: labor.fecha,
          contratista: labor.contratista,
          hectareas: labor.hectareas,
          costo_total: labor.costo_total,
          costo_dolares_ha: labor.costo_dolares_ha,
          costo_pesos_ha: labor.costo_pesos_ha,
          qq_ha: labor.qq_ha,
          observaciones: labor.observaciones
        });
        
        if (labor.insumos && labor.insumos.length > 0) {
          labor.insumos.forEach((insumo: any) => {
            this.agregarInsumo(insumo);
          });
        }
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando labor';
        this.loading = false;
      }
    });
  }

  get insumosArray(): FormArray {
    return this.insumosForm;
  }

  agregarInsumo(insumo?: any) {
    const insumoGroup = this.fb.group({
      insumo: [insumo?.insumo || '', Validators.required],
      dosis: [insumo?.dosis || 0, Validators.min(0)],
      unidad_dosis: [insumo?.unidad_dosis || 'l/ha'],
      total_aplicado: [insumo?.total_aplicado || 0, Validators.min(0)],
      precio_unitario: [insumo?.precio_unitario || 0, Validators.min(0)],
      costo_total: [insumo?.costo_total || 0]
    });
    this.insumosArray.push(insumoGroup);
  }

  eliminarInsumo(index: number) {
    this.insumosArray.removeAt(index);
  }

  guardar() {
    if (this.laborForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.laborForm.value;
    data.insumos = this.insumosArray.value;
    
    const request = this.isEdit && this.laborId
      ? this.api.put(`core/labores/${this.laborId}/`, data)
      : this.api.post('core/labores/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/labores']),
      error: () => {
        this.error = 'Error guardando labor';
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }
}
