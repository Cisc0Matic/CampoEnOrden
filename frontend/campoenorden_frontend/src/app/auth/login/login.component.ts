import { Component, NgZone, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule, NavController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, ReactiveFormsModule, RouterModule],
})
export class LoginComponent implements OnInit {
  ionViewWillLeave() {
    (document.activeElement as HTMLElement)?.blur();
  }

  loginForm: FormGroup;
  errorMessage: string | null = null;
  showPassword = false;
  loading = false;
  cuentaInactiva = false;
  reenvioLoading = false;
  reenvioExito = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private storage: Storage,
    private router: Router,
    private ngZone: NgZone,
    private navCtrl: NavController,
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });
  }

  async ngOnInit() {
    await this.storage.create();
    if (await this.authService.isLoggedIn()) {
      this.goToTabs();
    }
  }

  goToTabs() {
    this.ngZone.run(() => this.router.navigate(['/tabs']));
  }

  async onSubmit() {
    this.errorMessage = null;
    this.cuentaInactiva = false;
    this.reenvioExito = false;
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }
    this.loading = true;
    const { username, password } = this.loginForm.value;

    // Demo mode
    if (username === 'demo' && password === 'demo') {
      const fakeToken = 'demo_' + Date.now() + '_' + Math.random().toString(36).substring(2);
      localStorage.setItem('jwt_token', fakeToken);
      await this.storage.set('jwt_token', fakeToken);
      await this.storage.set('username', 'demo');
      this.loading = false;
      this.goToTabs();
      return;
    }

    try {
      await this.authService.login(username, password);
      this.goToTabs();
    } catch (error: any) {
      const detail = error?.error?.detail;
      if (detail === 'cuenta_no_activada') {
        this.cuentaInactiva = true;
      } else {
        this.errorMessage = detail || 'Credenciales inválidas.';
      }
    } finally {
      this.loading = false;
    }
  }

  async reenviarActivacion() {
    const username = this.loginForm.value.username;
    if (!username) return;
    this.reenvioLoading = true;
    try {
      await this.authService.resendActivationByUsername(username);
      this.reenvioExito = true;
      this.cuentaInactiva = false;
    } catch {
      this.errorMessage = 'No se pudo reenviar el email. Verificá el usuario ingresado.';
      this.cuentaInactiva = false;
    } finally {
      this.reenvioLoading = false;
    }
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  async clearToken() {
    localStorage.removeItem('jwt_token');
    await this.storage.remove('jwt_token');
    await this.storage.remove('username');
    this.router.navigate(['/login']);
  }
}
