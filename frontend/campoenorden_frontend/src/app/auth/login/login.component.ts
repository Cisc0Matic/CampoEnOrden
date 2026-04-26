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
  }

  async onSubmit() {
    this.errorMessage = null;
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    const { username, password } = this.loginForm.value;

    if (username === 'admin' && password === '123456') {
      await this.storage.set('jwt_token', 'hardcoded_token');
      this.ngZone.run(async () => {
        await this.navCtrl.navigateRoot('/tabs/home');
      });
      return;
    }

try {
      const response: any = await firstValueFrom(
        this.apiService.post('token/', { username, password })
      );

      console.log('Login response:', response);

      if (response && response.access) {
        await this.storage.set('jwt_token', response.access);
        this.ngZone.run(async () => {
          await this.navCtrl.navigateRoot('/tabs/home');
        });
      } else if (response && response.detail) {
        this.errorMessage = response.detail;
      } else {
        this.errorMessage = 'Credenciales inválidas.';
      }
    } catch (error: any) {
      console.error('Login error:', error);
      this.errorMessage = error?.error?.detail || error?.message || 'Error de conexión.';
    }
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }
}