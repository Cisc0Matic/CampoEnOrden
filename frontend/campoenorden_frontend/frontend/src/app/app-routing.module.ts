import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './auth/auth.guard'; // Import AuthGuard
import { LoginComponent } from './auth/login/login.component'; // Import LoginComponent

const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent 
  },
  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full'
  },
  {
    path: 'tabs', 
    loadChildren: () => import('./tabs/tabs.module').then(m => m.TabsPageModule),
    // CAMBIAMOS canLoad POR canActivate
    //canActivate: [AuthGuard] 
  },
  {
    path: 'labores',
    loadChildren: () => import('./labores/labores.module').then(m => m.LaboresModule),
    canLoad: [AuthGuard]
  },
  {
    path: '**',
    redirectTo: '/login'
  }
];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
