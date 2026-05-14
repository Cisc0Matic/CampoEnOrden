import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { CamposPage } from './campos.page';
import { CamposPageRoutingModule } from './campos-routing.module';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [CamposPage],
  imports: [
    IonicModule,
    CamposPageRoutingModule,
    SharedModule
  ]
})
export class CamposPageModule {}
