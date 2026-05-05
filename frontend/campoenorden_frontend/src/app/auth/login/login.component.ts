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
    
    // Si ya estamos en /login, no redirigir a tabs aunque haya token
    if (this.router.url.includes('/login')) {
      console.log('Ya estamos en login, mostrando login...');
      return;
    }
    
    const token = localStorage.getItem('jwt_token') || await this.storage.get('jwt_token');
    if (token) {
      console.log('Token encontrado, redirigiendo a tabs...');
      this.goToTabs();
    } else {
      console.log('No hay token, mostrando login...');
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
          this.apiService.post('token/', { username: 'admin', password: 'admin123' })
        );
      if (response && response.access) {
        localStorage.setItem('jwt_token', response.access);
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
      localStorage.setItem('jwt_token', response.access);
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
    console.log('Limpiando tokens...');
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('username');
    await this.storage.remove('jwt_token');
    await this.storage.remove('username');
    this.router.navigate(['/login']);
  }
}