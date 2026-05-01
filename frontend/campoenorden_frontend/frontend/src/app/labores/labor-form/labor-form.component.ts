import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule } from '@angular/forms'; // Import FormsModule

interface Lote {
  id: number;
  nombre: string;
}

interface Labor {
  id?: number;
  lote: number;
  fecha: string;
  tipo_aplicacion: string;
  insumos: string;
  costo: number;
  observaciones: string;
}

@Component({
  selector: 'app-labor-form',
  templateUrl: './labor-form.component.html',
  styleUrls: ['./labor-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, ReactiveFormsModule, FormsModule] // Add FormsModule here
})
export class LaborFormComponent implements OnInit {
  laborForm: FormGroup;
  laborId: number | null = null;
  lotes: Lote[] = [];
  loadingLotes = true;
  errorLotes: string | null = null;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.laborForm = this.fb.group({
      lote: ['', Validators.required],
      fecha: ['', Validators.required],
      tipo_aplicacion: ['', Validators.required],
      insumos: [''],
      costo: ['', [Validators.required, Validators.min(0)]],
      observaciones: ['']
    });
  }

  ngOnInit() {
    this.loadLotes();
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.laborId = +id;
        this.loadLabor(this.laborId);
      }
    });
  }

  loadLotes() {
    this.loadingLotes = true;
    this.errorLotes = null;
    this.apiService.get<Lote[]>('core/lotes/').subscribe({
      next: (data) => {
        this.lotes = data;
        this.loadingLotes = false;
      },
      error: (err) => {
        console.error('Error al cargar lotes:', err);
        this.errorLotes = 'No se pudieron cargar los lotes.';
        this.loadingLotes = false;
      }
    });
  }

  loadLabor(id: number) {
    this.apiService.get<Labor>(`labores/${id}/`).subscribe({
      next: (labor) => {
        this.laborForm.patchValue({
          lote: labor.lote,
          fecha: labor.fecha,
          tipo_aplicacion: labor.tipo_aplicacion,
          insumos: labor.insumos,
          costo: labor.costo,
          observaciones: labor.observaciones
        });
      },
      error: (err) => {
        console.error('Error al cargar labor:', err);
        // Manejar error, quizás redirigir o mostrar mensaje
      }
    });
  }

  saveLabor() {
    if (this.laborForm.valid) {
      const laborData: Labor = this.laborForm.value;
      if (this.laborId) {
        // Actualizar labor existente
        this.apiService.put<Labor>(`labores/${this.laborId}/`, laborData).subscribe({
          next: () => {
            this.router.navigate(['/labores']);
          },
          error: (err) => {
            console.error('Error al actualizar labor:', err);
            // Manejar error
          }
        });
      } else {
        // Crear nueva labor
        this.apiService.post<Labor>('labores/', laborData).subscribe({
          next: () => {
            this.router.navigate(['/labores']);
          },
          error: (err) => {
            console.error('Error al crear labor:', err);
            // Manejar error
          }
        });
      }
    } else {
      this.laborForm.markAllAsTouched();
    }
  }

  goBack() {
    this.router.navigate(['/labores']);
  }
}