import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../../services/api.service';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonicModule,
    MatButtonModule,
    MatListModule,
    MatIconModule
  ]
})
export class HomeComponent implements OnInit {
  data: any[] = [];
  errorMessage: string | null = null;

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.fetchProtectedData();
  }

  fetchProtectedData() {
    this.errorMessage = null;
    // Assuming a protected endpoint like 'users/' or 'campos/'
    // For this example, let's try to fetch users from the backend
    interface User {
      id: number;
      username: string;
      email: string;
      role: string;
    }

    this.apiService.get<User[]>('users/').subscribe({ // Specify the expected type as User[]
      next: (response) => {
        this.data = response;
        console.log('Datos protegidos:', response);
      },
      error: (error) => {
        console.error('Error al obtener datos protegidos:', error);
        this.errorMessage = 'Error al cargar datos. ¿Estás autenticado?';
      }
    });
  }
}
