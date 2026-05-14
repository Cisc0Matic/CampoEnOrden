import type { Meta } from '@storybook/angular';

const meta: Meta = {
  title: 'Design System/Tokens',
  parameters: {
    docs: {
      description: {
        component: 'Design tokens del sistema CampoEnOrden',
      },
    },
  },
};

export default meta;

export const Colors = () => ({
  template: `
    <div style="padding: 24px; font-family: 'Inter', sans-serif;">
      <h2 style="margin-bottom: 16px;">Paleta de Colores</h2>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
        <div *ngFor="let color of colors" style="text-align: center;">
          <div [style.background]="color.value" style="height: 60px; border-radius: 8px; margin-bottom: 4px; border: 1px solid #e0e0e0;"></div>
          <div style="font-size: 12px; font-weight: 600;">{{color.name}}</div>
          <div style="font-size: 11px; color: #666;">{{color.value}}</div>
        </div>
      </div>
    </div>
  `,
  props: {
    colors: [
      { name: 'Primary', value: '#2E7D32' },
      { name: 'Primary Light', value: '#4CAF50' },
      { name: 'Primary Dark', value: '#1B5E20' },
      { name: 'Secondary', value: '#4CAF50' },
      { name: 'Tertiary', value: '#A5D6A7' },
      { name: 'Success', value: '#10dc60' },
      { name: 'Warning', value: '#ffce00' },
      { name: 'Danger', value: '#f04141' },
      { name: 'Dark', value: '#222428' },
      { name: 'Medium', value: '#989aa2' },
      { name: 'Light', value: '#f4f5f8' },
      { name: 'Background', value: '#f5f5f5' },
    ],
  },
});

export const Typography = () => ({
  template: `
    <div style="padding: 24px; font-family: 'Inter', sans-serif;">
      <h2 style="margin-bottom: 16px;">Tipografía</h2>
      <div style="margin-bottom: 24px;">
        <div style="font-size: 28px; font-weight: 700;">Heading 1 (28px Bold)</div>
        <div style="font-size: 22px; font-weight: 700; margin-top: 12px;">Heading 2 (22px Bold)</div>
        <div style="font-size: 18px; font-weight: 600; margin-top: 12px;">Heading 3 (18px Semibold)</div>
        <div style="font-size: 16px; font-weight: 600; margin-top: 12px;">Heading 4 (16px Semibold)</div>
        <div style="font-size: 14px; margin-top: 12px;">Body (14px Regular)</div>
        <div style="font-size: 12px; margin-top: 12px;">Body Small (12px Regular)</div>
        <div style="font-size: 11px; color: #666; margin-top: 12px;">Caption (11px)</div>
        <div style="font-size: 10px; color: #666; margin-top: 12px;">Small (10px)</div>
      </div>
      <div style="padding: 16px; background: #f5f5f5; border-radius: 8px;">
        <p style="margin: 0;"><strong>Font:</strong> Inter</p>
        <p style="margin: 4px 0 0; color: #666;">Disponible en pesos: 300, 400, 500, 600, 700</p>
      </div>
    </div>
  `,
});
