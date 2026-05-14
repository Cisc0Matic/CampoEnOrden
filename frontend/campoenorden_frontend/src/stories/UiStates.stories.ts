import type { Meta, StoryObj } from '@storybook/angular';
import { UiLoadingStateComponent } from '../app/shared/components/ui-loading-state/ui-loading-state.component';
import { UiErrorStateComponent } from '../app/shared/components/ui-error-state/ui-error-state.component';
import { UiEmptyStateComponent } from '../app/shared/components/ui-empty-state/ui-empty-state.component';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';
import { moduleMetadata } from '@storybook/angular';

export default {
  title: 'Components/States',
  decorators: [
    moduleMetadata({
      imports: [CommonModule, IonicModule.forRoot()],
    }),
  ],
} as Meta;

export const Loading: StoryObj<UiLoadingStateComponent> = {
  render: () => ({
    moduleMetadata: { imports: [CommonModule, IonicModule.forRoot(), UiLoadingStateComponent] },
    template: `<ui-loading-state message="Cargando datos..."></ui-loading-state>`,
  }),
};

export const Error: StoryObj<UiErrorStateComponent> = {
  render: () => ({
    moduleMetadata: { imports: [CommonModule, IonicModule.forRoot(), UiErrorStateComponent] },
    template: `<ui-error-state message="No se pudieron cargar los datos"></ui-error-state>`,
  }),
};

export const Empty: StoryObj<UiEmptyStateComponent> = {
  render: () => ({
    moduleMetadata: { imports: [CommonModule, IonicModule.forRoot(), UiEmptyStateComponent] },
    template: `
      <ui-empty-state
        icon="leaf-outline"
        title="No hay campos cargados"
        actionLabel="Agregar Campo"
      ></ui-empty-state>
    `,
  }),
};
