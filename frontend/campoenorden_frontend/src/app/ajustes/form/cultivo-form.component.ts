import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ModalController } from '@ionic/angular';

@Component({
  selector: 'app-cultivo-form',
  templateUrl: './cultivo-form.component.html',
  styleUrls: ['./cultivo-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class CultivoFormComponent {
  form: FormGroup;
  loading = false;
  error: string | null = null;

  familias = ['GRAMINEA', 'LEGUMINOSA', 'OLEAGINOSA', 'OTRA'];
  ciclos = ['GRUESA', 'FINA', 'INVIERNO', 'VERANO'];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private modalCtrl: ModalController
  ) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      familia: ['OTRA'],
      ciclo: ['GRUESA'],
      activo: [true]
    });
  }

  guardar() {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    this.loading = true;
    this.error = null;
    this.api.post('core/cultivos/', this.form.value).subscribe({
      next: async (res) => {
        await this.modalCtrl.dismiss(res, 'created');
      },
      error: () => {
        this.error = 'Error al crear cultivo';
        this.loading = false;
      }
    });
  }

  cancelar() {
    this.modalCtrl.dismiss(null, 'cancel');
  }
}
