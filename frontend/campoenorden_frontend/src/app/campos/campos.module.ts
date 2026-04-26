import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { CamposPage } from './campos.page';
import { CamposPageRoutingModule } from './campos-routing.module';

@NgModule({
  declarations: [CamposPage],
  imports: [
    IonicModule,
    CamposPageRoutingModule
  ]
})
export class CamposPageModule {}