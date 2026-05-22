import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule, ModalController, ToastController } from '@ionic/angular';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../../services/api.service';

@Component({
  selector: 'app-crear-persona-modal',
  templateUrl: './crear-persona-modal.component.html',
  styleUrls: ['./crear-persona-modal.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule]
})
export class CrearPersonaModalComponent {
  @Input() rol = '';

  personaForm: FormGroup;
  loading = false;
  error: string | null = null;
  tipos = [
    { value: 'PERSONA', label: 'Persona' },
    { value: 'EMPRESA', label: 'Empresa' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private modalCtrl: ModalController,
    private toastCtrl: ToastController
  ) {
    this.personaForm = this.fb.group({
      nombre: ['', Validators.required],
      tipo: ['PERSONA'],
      documento: [''],
      cuil: [''],
      telefono: [''],
      email: ['', Validators.email]
    });
  }

  guardar() {
    if (this.personaForm.invalid) return;

    this.loading = true;
    this.error = null;
    const data = {
      ...this.personaForm.value,
      rol: this.rol,
      activo: true
    };

    this.api.post('core/personas/', data).subscribe({
      next: async (persona: any) => {
        if (!persona || !persona.id) {
          this.error = 'Error al crear persona';
          this.loading = false;
          return;
        }
        const toast = await this.toastCtrl.create({
          message: 'Persona creada correctamente',
          duration: 1500,
          color: 'success'
        });
        await toast.present();
        this.modalCtrl.dismiss(persona);
      },
      error: async () => {
        this.error = 'Error al crear persona';
        this.loading = false;
      }
    });
  }

  cerrar() {
    this.modalCtrl.dismiss();
  }
}
