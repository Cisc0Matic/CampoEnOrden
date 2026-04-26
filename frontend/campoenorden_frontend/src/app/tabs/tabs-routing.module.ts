import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TabsPage } from './tabs.page';

const routes: Routes = [
  {
    path: '',
    component: TabsPage,
    children: [
      {
        path: 'inicio',
        loadComponent: () => import('../dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'campos',
        loadComponent: () => import('../campos/campos.page').then(m => m.CamposPage)
      },
      {
        path: 'lotes',
        loadComponent: () => import('../lotes/lotes.page').then(m => m.LotesPage)
      },
      {
        path: 'labores',
        loadComponent: () => import('../labores/labores.page').then(m => m.LaboresPage)
      },
      {
        path: 'logistica',
        loadComponent: () => import('../logistica/logistica.page').then(m => m.LogisticaPage)
      },
      {
        path: 'documentos',
        loadComponent: () => import('../documentos/documentos.page').then(m => m.DocumentosPage)
      },
      {
        path: 'usuarios',
        loadComponent: () => import('../usuarios/usuarios.page').then(m => m.UsuariosPage)
      },
      {
        path: 'ajustes',
        loadComponent: () => import('../ajustes/ajustes.page').then(m => m.AjustesPage)
      },
      {
        path: '',
        redirectTo: 'inicio',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '',
    redirectTo: 'inicio',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TabsPageRoutingModule {}