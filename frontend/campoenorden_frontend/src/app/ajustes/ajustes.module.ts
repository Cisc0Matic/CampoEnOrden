import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { AjustesPage } from './ajustes.page';

const routes: Routes = [{ path: '', component: AjustesPage }];

@NgModule({
  imports: [
    IonicModule,
    RouterModule.forChild(routes)
  ],
  exports: [RouterModule]
})
export class AjustesPageModule {}