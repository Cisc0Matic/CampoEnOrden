import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { LaboresPage } from './labores.page';

const routes: Routes = [{ path: '', component: LaboresPage }];

@NgModule({
  imports: [
    IonicModule,
    RouterModule.forChild(routes)
  ],
  exports: [RouterModule]
})
export class LaboresPageModule {}