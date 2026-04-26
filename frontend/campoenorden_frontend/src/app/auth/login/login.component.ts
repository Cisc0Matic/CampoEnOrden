import { Component, OnInit, NgZone } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { IonicModule, NavController } from '@ionic/angular';
import { ApiService } from '../../services/api.service';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, ReactiveFormsModule]
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  errorMessage: string | null = null;
  showPassword = false;
  loading = false;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private storage: Storage,
    private router: Router,
    private ngZone: NgZone,
    private navCtrl: NavController
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  async ngOnInit() {
    await this.storage.create();
    
    const token = await this.storage.get('jwt_token');
    if (token) {
      console.log('Ya hay token, redirigiendo...');
      this.goToTabs();
    }
  }

  goToTabs() {
    this.ngZone.run(() => {
      this.router.navigate(['/tabs']);
    });
  }

  async onSubmit() {
    this.errorMessage = null;
    this.loading = true;
    
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      this.loading = false;
      return;
    }

    const { username, password } = this.loginForm.value;

    // LOGIN DE EMERGENCIA - QUITAR EN PRODUCCIÓN
    if (username === 'demo' && password === 'demo') {
      try {
        const response: any = await firstValueFrom(
          this.apiService.post('token/', { username: 'demo', password: 'demo123' })
        );
        if (response && response.access) {
          await this.storage.set('jwt_token', response.access);
          await this.storage.set('username', username);
          this.goToTabs();
        }
      } catch (error) {
        this.errorMessage = 'Demo no disponible. ¿Backend corriendo?';
      }
      this.loading = false;
      return;
    }

    try {
      const response: any = await firstValueFrom(
        this.apiService.post('token/', { username, password })
      );

      console.log('Login response:', response);

      if (response && response.access) {
        await this.storage.set('jwt_token', response.access);
        await this.storage.set('username', username);
        this.goToTabs();
      } else if (response && response.detail) {
        this.errorMessage = response.detail;
      } else {
        this.errorMessage = 'Credenciales inválidas.';
      }
    } catch (error: any) {
      console.error('Login error:', error);
      this.errorMessage = 'Error de conexión. ¿Backend corriendo?';
    } finally {
      this.loading = false;
    }
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }
  
  async clearToken() {
    await this.storage.remove('jwt_token');
    window.location.reload();
  }
}