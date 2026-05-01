import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';

interface Persona {
  id: number;
  nombre: string;
  tipo: string;
  rol: string;
  nombre_rol: string;
  documento: string;
  cuil: string;
  direccion: string;
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
  personasFiltradas: Persona[] = [];
  loading = true;
  error: string | null = null;
  filtroRol = '';
  filtroTipo = '';

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.cargarPersonas();
  }

  cargarPersonas() {
    this.loading = true;
    this.api.get<Persona[]>('core/personas/').subscribe({
      next: (data) => {
        this.personas = data || [];
        this.filtrarPersonas();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar personas';
        this.loading = false;
      }
    });
  }

  filtrarPersonas() {
    this.personasFiltradas = this.personas.filter(p => {
      if (this.filtroRol && p.rol !== this.filtroRol) return false;
      if (this.filtroTipo && p.tipo !== this.filtroTipo) return false;
      return true;
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

  agregarPersona() {
    this.router.navigate(['/tabs/usuarios/crear']);
  }

  editarPersona(persona: Persona) {
    this.router.navigate(['/tabs/usuarios/editar', persona.id]);
  }

  verDetallePersona(persona: Persona) {
    this.router.navigate(['/tabs/usuarios', persona.id]);
  }

  toggleActivo(persona: Persona) {
    this.api.put(`core/personas/${persona.id}/`, { activo: !persona.activo }).subscribe({
      next: () => this.cargarPersonas(),
      error: () => console.error('Error actualizando estado')
    });
  }
}