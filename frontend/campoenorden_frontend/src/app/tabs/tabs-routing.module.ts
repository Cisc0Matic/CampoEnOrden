import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TabsPage } from './tabs.page';
import { AuthGuard } from '../auth/auth.guard';

const routes: Routes = [
  {
    path: '',
    component: TabsPage,
    canActivate: [AuthGuard],
    children: [
      {
        path: 'inicio',
        loadComponent: () => import('../dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
       {
         path: 'campos',
         children: [
           {
             path: '',
             loadComponent: () => import('../campos/campos.page').then(m => m.CamposPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../campos/form/campo-form.component').then(m => m.CampoFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../campos/form/campo-form.component').then(m => m.CampoFormComponent)
           }
         ]
       },
       {
         path: 'lotes',
         children: [
           {
             path: '',
             loadComponent: () => import('../lotes/lotes.page').then(m => m.LotesPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../lotes/form/lote-form.component').then(m => m.LoteFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../lotes/form/lote-form.component').then(m => m.LoteFormComponent)
           }
         ]
       },
       {
         path: 'labores',
         children: [
           {
             path: '',
             loadComponent: () => import('../labores/labores.page').then(m => m.LaboresPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../labores/form/labor-form.component').then(m => m.LaborFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../labores/form/labor-form.component').then(m => m.LaborFormComponent)
           }
         ]
       },
       {
         path: 'logistica',
         children: [
           {
             path: '',
             loadComponent: () => import('../logistica/logistica.page').then(m => m.LogisticaPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../logistica/form/flete-form.component').then(m => m.FleteFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../logistica/form/flete-form.component').then(m => m.FleteFormComponent)
           }
         ]
       },
       {
         path: 'documentos',
         children: [
           {
             path: '',
             loadComponent: () => import('../documentos/documentos.page').then(m => m.DocumentosPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../documentos/form/documento-form.component').then(m => m.DocumentoFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../documentos/form/documento-form.component').then(m => m.DocumentoFormComponent)
           }
         ]
       },
       {
         path: 'usuarios',
         children: [
           {
             path: '',
             loadComponent: () => import('../usuarios/usuarios.page').then(m => m.UsuariosPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../usuarios/form/persona-form.component').then(m => m.PersonaFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../usuarios/form/persona-form.component').then(m => m.PersonaFormComponent)
           }
         ]
       },
       {
         path: 'ajustes',
         children: [
           {
             path: '',
             loadComponent: () => import('../ajustes/ajustes.page').then(m => m.AjustesPage)
           },
           {
             path: 'crear',
             loadComponent: () => import('../ajustes/form/parametro-form.component').then(m => m.ParametroFormComponent)
           },
           {
             path: 'editar/:id',
             loadComponent: () => import('../ajustes/form/parametro-form.component').then(m => m.ParametroFormComponent)
           }
         ]
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