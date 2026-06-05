import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, ReactiveFormsModule, RouterModule],
})
export class RegisterComponent {
  form: FormGroup;
  loading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;
  showPassword = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
  ) {
    this.form = this.fb.group({
      empresa_nombre: ['', Validators.required],
      first_name: ['', Validators.required],
      last_name: [''],
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password_confirm: ['', Validators.required],
    });
  }

  async onSubmit() {
    this.errorMessage = null;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.form.value.password !== this.form.value.password_confirm) {
      this.errorMessage = 'Las contraseñas no coinciden.';
      return;
    }
    this.loading = true;
    try {
      await this.authService.register(this.form.value);
      this.successMessage = `Cuenta creada. Revisá ${this.form.value.email} para activarla.`;
    } catch (error: any) {
      this.errorMessage = this._parseError(error);
    } finally {
      this.loading = false;
    }
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  private _parseError(error: any): string {
    const data = error?.error;
    if (!data) return 'Error de conexión.';
    if (typeof data === 'string') return data;
    const firstKey = Object.keys(data)[0];
    const msg = data[firstKey];
    return Array.isArray(msg) ? msg[0] : String(msg);
  }
}
