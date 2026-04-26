import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { DocumentosPage } from './documentos.page';

const routes: Routes = [{ path: '', component: DocumentosPage }];

@NgModule({
  imports: [
    IonicModule,
    RouterModule.forChild(routes)
  ],
  exports: [RouterModule]
})
export class DocumentosPageModule {}