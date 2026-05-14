import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { UiCardComponent } from './components/ui-card/ui-card.component';
import { UiHeaderComponent } from './components/ui-header/ui-header.component';
import { UiEmptyStateComponent } from './components/ui-empty-state/ui-empty-state.component';
import { UiErrorStateComponent } from './components/ui-error-state/ui-error-state.component';
import { UiLoadingStateComponent } from './components/ui-loading-state/ui-loading-state.component';
import { UiFormActionsComponent } from './components/ui-form-actions/ui-form-actions.component';
import { UiConfirmDeleteComponent } from './components/ui-confirm-delete/ui-confirm-delete.component';

@NgModule({
  imports: [
    CommonModule,
    IonicModule,
    UiCardComponent,
    UiHeaderComponent,
    UiEmptyStateComponent,
    UiErrorStateComponent,
    UiLoadingStateComponent,
    UiFormActionsComponent,
    UiConfirmDeleteComponent,
  ],
  exports: [
    UiCardComponent,
    UiHeaderComponent,
    UiEmptyStateComponent,
    UiErrorStateComponent,
    UiLoadingStateComponent,
    UiFormActionsComponent,
    UiConfirmDeleteComponent,
  ],
})
export class SharedModule {}
