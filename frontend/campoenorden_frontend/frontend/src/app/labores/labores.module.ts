import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { LaboresRoutingModule } from './labores-routing.module';
import { LaborListComponent } from './labor-list/labor-list.component';
import { LaborFormComponent } from './labor-form/labor-form.component'; // Import LaborFormComponent

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    LaboresRoutingModule,
    LaborFormComponent // Import LaborFormComponent as it's standalone
  ],
  declarations: [] // LaborListComponent is standalone, so no need to declare here
})
export class LaboresModule { }
