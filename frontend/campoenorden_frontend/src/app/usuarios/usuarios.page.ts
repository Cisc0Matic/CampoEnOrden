import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';

interface Persona {
  id: number;
  nombre: string;
  tipo: string;
  rol: string;
  nombre_rol: string;
  documento: string;
  cuil: string;
  telefono: string;
  email: string;
  activo: boolean;
}

@Component({
  selector: 'app-usuarios',
  templateUrl: './usuarios.page.html',
  styleUrls: ['./usuarios.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule]
})
export class UsuariosPage implements OnInit {
  personas: Persona[] = [];
  loading = true;
  error: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.cargarPersonas();
  }

  cargarPersonas() {
    this.loading = true;
    this.api.get<Persona[]>('core/personas/').subscribe({
      next: (data) => {
        this.personas = data || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar personas';
        this.loading = false;
      }
    });
  }

  getRolIcon(rol: string): string {
    switch (rol) {
      case 'DUENO': return 'person';
      case 'ARRENDATARIO': return 'key';
      case 'CONTRATISTA': return 'construct';
      case 'CHOFER': return 'car';
      case 'ADMINISTRADOR': return 'shield';
      default: return 'person';
    }
  }
}