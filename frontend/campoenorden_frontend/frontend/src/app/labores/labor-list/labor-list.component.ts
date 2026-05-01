import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

interface Labor {
  id: number;
  lote: number;
  fecha: string;
  tipo_aplicacion: string;
  insumos: string;
  costo: number;
  observaciones: string;
}

@Component({
  selector: 'app-labor-list',
  templateUrl: './labor-list.component.html',
  styleUrls: ['./labor-list.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class LaborListComponent implements OnInit {
  labores: Labor[] = [];
  loading = true;
  error: string | null = null;

  constructor(private apiService: ApiService, private router: Router) { }

  ngOnInit() {
    this.loadLabores();
  }

  loadLabores() {
    this.loading = true;
    this.error = null;
    this.apiService.get<Labor[]>('labores/').subscribe({
      next: (data) => {
        this.labores = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error al cargar labores:', err);
        this.error = 'No se pudieron cargar las labores. Intente de nuevo más tarde.';
        this.loading = false;
      }
    });
  }

  addLabor() {
    this.router.navigate(['/labores/new']);
  }

  editLabor(id: number) {
    this.router.navigate(['/labores/edit', id]);
  }

  deleteLabor(id: number) {
    if (confirm('¿Está seguro de que desea eliminar esta labor?')) {
      this.apiService.delete(`labores/${id}/`).subscribe({
        next: () => {
          this.labores = this.labores.filter(labor => labor.id !== id);
        },
        error: (err) => {
          console.error('Error al eliminar labor:', err);
          this.error = 'No se pudo eliminar la labor. Intente de nuevo más tarde.';
        }
      });
    }
  }
}
