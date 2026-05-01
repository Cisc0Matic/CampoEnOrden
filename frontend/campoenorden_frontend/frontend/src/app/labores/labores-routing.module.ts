import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { LaborListComponent } from './labor-list/labor-list.component';
import { LaborFormComponent } from './labor-form/labor-form.component';

const routes: Routes = [
  {
    path: '',
    component: LaborListComponent
  },
  {
    path: 'new',
    component: LaborFormComponent
  },
  {
    path: 'edit/:id',
    component: LaborFormComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class LaboresRoutingModule { }
