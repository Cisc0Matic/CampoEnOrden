import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-invite',
  templateUrl: './invite.component.html',
  styleUrls: ['./invite.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, ReactiveFormsModule, RouterModule],
})
export class InviteComponent implements OnInit {
  form: FormGroup;
  token = '';
  inviteInfo: { email: string; role_display: string; empresa: string } | null = null;
  loading = false;
  checking = true;
  done = false;
  showPassword = false;
  errorMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private route: ActivatedRoute,
  ) {
    this.form = this.fb.group({
      first_name: ['', Validators.required],
      last_name: [''],
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password_confirm: ['', Validators.required],
    });
  }

  async ngOnInit() {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) {
      this.errorMessage = 'Enlace de invitación inválido.';
      this.checking = false;
      return;
    }
    try {
      this.inviteInfo = await this.authService.getInvitationInfo(this.token);
    } catch (error: any) {
      this.errorMessage = error?.error?.detail || 'La invitación es inválida o expiró.';
    } finally {
      this.checking = false;
    }
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
      await this.authService.acceptInvitation({ token: this.token, ...this.form.value });
      this.done = true;
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
