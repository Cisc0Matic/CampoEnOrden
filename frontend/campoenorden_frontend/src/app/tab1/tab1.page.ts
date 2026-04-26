import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

interface MosaicItem {
  id: string;
  title: string;
  icon: string;
  color: string;
  route: string;
  description: string;
}

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss'],
  standalone: false,
})
export class Tab1Page {

  mosaicItems: MosaicItem[] = [
    {
      id: 'campos',
      title: 'Campos',
      icon: 'grid',
      color: '#2E7D32',
      route: '/tabs/tab2',
      description: 'Gestión de campos'
    },
    {
      id: 'lotes',
      title: 'Lotes',
      icon: 'layers',
      color: '#1565C0',
      route: '/tabs/tab2',
      description: 'Administración de lotes'
    },
    {
      id: 'labores',
      title: 'Labores',
      icon: 'construct',
      color: '#EF6C00',
      route: '/labores',
      description: 'Control de labores'
    },
    {
      id: 'logistica',
      title: 'Logística',
      icon: 'truck',
      color: '#6A1B9A',
      route: '/tabs/tab3',
      description: 'Fletes y transporte'
    },
    {
      id: 'usuarios',
      title: 'Usuarios',
      icon: 'people',
      color: '#C62828',
      route: '/tabs/tab3',
      description: 'Gestión de usuarios'
    },
    {
      id: 'documentos',
      title: 'Documentos',
      icon: 'document-text',
      color: '#00838F',
      route: '/tabs/tab3',
      description: 'Documentos y reportes'
    },
    {
      id: 'ajustes',
      title: 'Ajustes',
      icon: 'settings',
      color: '#455A64',
      route: '/tabs/tab3',
      description: 'Configuración del sistema'
    }
  ];

  constructor(private router: Router, private authService: AuthService) {}

  navigateTo(route: string) {
    this.router.navigateByUrl(route);
  }

  logout() {
    this.authService.logout();
  }

  getIconName(icon: string): string {
    const iconMap: { [key: string]: string } = {
      'grid': 'apps',
      'layers': 'layers',
      'construct': 'build',
      'truck': 'local-shipping',
      'people': 'people',
      'document-text': 'document-text',
      'settings': 'settings'
    };
    return iconMap[icon] || 'ellipse';
  }
}
