import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-activate',
  templateUrl: './activate.component.html',
  styleUrls: ['./activate.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, RouterModule],
})
export class ActivateComponent implements OnInit {
  state: 'loading' | 'success' | 'error' = 'loading';
  errorMessage = '';

  constructor(
    private authService: AuthService,
    private route: ActivatedRoute,
  ) {}

  async ngOnInit() {
    const token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!token) {
      this.state = 'error';
      this.errorMessage = 'El enlace de activación es inválido.';
      return;
    }
    try {
      await this.authService.activateAccount(token);
      this.state = 'success';
    } catch (error: any) {
      this.state = 'error';
      const data = error?.error;
      if (data?.token) {
        this.errorMessage = Array.isArray(data.token) ? data.token[0] : data.token;
      } else {
        this.errorMessage = 'No se pudo activar la cuenta. El enlace puede haber expirado.';
      }
    }
  }
}
