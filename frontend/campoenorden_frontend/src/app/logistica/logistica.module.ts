import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { LogisticaPage } from './logistica.page';

const routes: Routes = [{ path: '', component: LogisticaPage }];

@NgModule({
  imports: [
    IonicModule,
    RouterModule.forChild(routes)
  ],
  exports: [RouterModule]
})
export class LogisticaPageModule {}