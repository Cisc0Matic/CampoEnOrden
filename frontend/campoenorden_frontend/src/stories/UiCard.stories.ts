import type { Meta, StoryObj } from '@storybook/angular';
import { UiCardComponent } from '../app/shared/components/ui-card/ui-card.component';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';
import { moduleMetadata } from '@storybook/angular';

const meta: Meta<UiCardComponent> = {
  title: 'Components/Card',
  component: UiCardComponent,
  decorators: [
    moduleMetadata({
      imports: [CommonModule, IonicModule.forRoot()],
    }),
  ],
  argTypes: {
    color: {
      control: 'select',
      options: ['primary', 'secondary', 'tertiary', 'success', 'warning', 'danger', 'medium'],
    },
  },
};

export default meta;
type Story = StoryObj<UiCardComponent>;

export const Primary: Story = {
  args: { color: 'primary' },
  render: (args) => ({
    props: args,
    template: `
      <div style="padding: 24px; max-width: 400px;">
        <ui-card [color]="color">
          <div card-header>
            <div style="display: flex; align-items: center; gap: 8px; color: white;">
              <ion-icon name="leaf"></ion-icon>
              <span style="font-weight: 600;">Campo San José</span>
            </div>
            <ion-badge color="light">Activo</ion-badge>
          </div>
          <div card-body>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: #989aa2; margin-bottom: 4px;">
              <ion-icon name="location"></ion-icon>
              <span>Ruta 8, Km 120</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0;">
              <div style="background: #f0f0f0; border-radius: 10px; padding: 10px; text-align: center;">
                <span style="display: block; font-size: 16px; font-weight: 700;">100</span>
                <span style="display: block; font-size: 10px; color: #989aa2;">ha total</span>
              </div>
              <div style="background: #f0f0f0; border-radius: 10px; padding: 10px; text-align: center;">
                <span style="display: block; font-size: 16px; font-weight: 700;">80</span>
                <span style="display: block; font-size: 10px; color: #989aa2;">ha trab</span>
              </div>
            </div>
          </div>
          <div card-footer>
            <ion-button fill="clear" size="small">
              <ion-icon slot="start" name="document-text"></ion-icon>
              Docs (3)
            </ion-button>
            <ion-button fill="clear" size="small">
              <ion-icon slot="start" name="create"></ion-icon>
              Editar
            </ion-button>
          </div>
        </ui-card>
      </div>
    `,
  }),
};

export const WithWarningColor: Story = {
  args: { color: 'warning' },
  render: (args) => ({
    props: args,
    template: `
      <div style="padding: 24px; max-width: 400px;">
        <ui-card [color]="color">
          <div card-header>
            <div style="display: flex; align-items: center; gap: 8px; color: white;">
              <ion-icon name="warning"></ion-icon>
              <span style="font-weight: 600;">Alerta de Contrato</span>
            </div>
            <ion-badge color="light">Pendiente</ion-badge>
          </div>
          <div card-body>
            <p style="margin: 0; font-size: 14px; color: #666;">
              Este campo tiene un contrato próximo a vencer. Revisa la documentación pendiente.
            </p>
          </div>
          <div card-footer>
            <ion-button fill="clear" size="small">Revisar</ion-button>
          </div>
        </ui-card>
      </div>
    `,
  }),
};
