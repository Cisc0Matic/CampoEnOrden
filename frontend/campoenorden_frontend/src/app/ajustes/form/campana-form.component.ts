import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ModalController } from '@ionic/angular';

@Component({
  selector: 'app-campana-form',
  templateUrl: './campana-form.component.html',
  styleUrls: ['./campana-form.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class CampanaFormComponent {
  form: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private modalCtrl: ModalController
  ) {
    this.form = this.fb.group({
      nombre: ['', Validators.required],
      inicio: [''],
      fin: [''],
      activa: [true]
    });
  }

  guardar() {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    this.loading = true;
    this.error = null;
    this.api.post('core/campanas/', this.form.value).subscribe({
      next: async (res) => {
        await this.modalCtrl.dismiss(res, 'created');
      },
      error: () => {
        this.error = 'Error al crear campaña';
        this.loading = false;
      }
    });
  }

  cancelar() {
    this.modalCtrl.dismiss(null, 'cancel');
  }
}
