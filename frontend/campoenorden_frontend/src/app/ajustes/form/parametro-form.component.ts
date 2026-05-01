import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-parametro-form',
  templateUrl: './parametro-form.component.html',
  styleUrls: ['./parametro-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class ParametroFormComponent implements OnInit {
  parametroForm: FormGroup;
  isEdit = false;
  parametroId: string | null = null;
  loading = false;
  error: string | null = null;
  campanas: any[] = [];
  categorias = [
    { value: 'GRANO', label: 'Granos' },
    { value: 'INSUMO', label: 'Insumos' },
    { value: 'LABOR', label: 'Labores' },
    { value: 'COMERCIALIZACION', label: 'Comercialización' },
    { value: 'COSECHA', label: 'Cosecha' },
    { value: 'TIPO_CAMBIO', label: 'Tipo Cambio' },
    { value: 'UNIDAD', label: 'Unidades' }
  ];
  unidades: string[] = ['$/tn', 'U$S/tn', '$/ha', 'U$S/ha', 'l/ha', 'kg/ha', 'g/ha', 'qq/ha', 'unidades/ha'];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    public router: Router
  ) {
    this.parametroForm = this.fb.group({
      nombre: ['', Validators.required],
      categoria: ['', Validators.required],
      valor: [0, [Validators.required, Validators.min(0)]],
      unidad: ['', Validators.required],
      campana: [null],
      vigente: [true]
    });
  }

  ngOnInit() {
    this.parametroId = this.route.snapshot.paramMap.get('id');
    this.isEdit = this.route.snapshot.url.some(segment => segment.path === 'editar');
    
    this.api.get<any[]>('core/campanas/').subscribe({
      next: (campanas) => {
        this.campanas = campanas || [];
        if (this.isEdit && this.parametroId) {
          this.cargarParametro();
        }
      },
      error: () => this.loading = false
    });

    this.route.queryParams.subscribe(params => {
      if (params['nombre'] && params['categoria']) {
        this.parametroForm.patchValue({
          nombre: params['nombre'],
          categoria: params['categoria']
        });
      }
    });
  }

  cargarParametro() {
    if (!this.parametroId) return;
    this.loading = true;
    this.api.get<any>(`core/parametros/${this.parametroId}/`).subscribe({
      next: (parametro) => {
        this.parametroForm.patchValue({
          nombre: parametro.nombre,
          categoria: parametro.categoria,
          valor: parametro.valor,
          unidad: parametro.unidad,
          campana: parametro.campana,
          vigente: parametro.vigente
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Error cargando parámetro';
        this.loading = false;
      }
    });
  }

  guardar() {
    if (this.parametroForm.invalid) {
      this.error = 'Por favor complete los campos requeridos';
      return;
    }

    this.loading = true;
    const data = this.parametroForm.value;
    
    const request = this.isEdit && this.parametroId
      ? this.api.put(`core/parametros/${this.parametroId}/`, data)
      : this.api.post('core/parametros/', data);

    request.subscribe({
      next: () => this.router.navigate(['/tabs/ajustes']),
      error: () => {
        this.error = 'Error guardando parámetro';
        this.loading = false;
      }
    });
  }

  compararPorId(item1: any, item2: any): boolean {
    return item1 && item2 ? item1.id === item2.id : item1 === item2;
  }
}
