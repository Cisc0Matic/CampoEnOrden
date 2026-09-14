import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class DeleteConfirmService {
  constructor(private alertCtrl: AlertController, private auth: AuthService) {}

  /** Pide confirmación y luego la contraseña del usuario. Devuelve true solo si ambas se cumplen. */
  async confirmar(nombre: string): Promise<boolean> {
    const confirmado = await this.mostrarConfirmacion(nombre);
    if (!confirmado) return false;
    return this.pedirClave();
  }

  private mostrarConfirmacion(nombre: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.alertCtrl.create({
        header: 'Eliminar',
        message: `¿Estás seguro de que querés eliminar "${nombre}"? Esta acción no se puede deshacer.`,
        buttons: [
          { text: 'Cancelar', role: 'cancel', handler: () => resolve(false) },
          { text: 'Eliminar', role: 'destructive', handler: () => resolve(true) },
        ],
      }).then(a => a.present());
    });
  }

  private pedirClave(): Promise<boolean> {
    return new Promise((resolve) => {
      this.alertCtrl.create({
        header: 'Confirmá tu contraseña',
        message: 'Por seguridad, ingresá tu contraseña para continuar con la eliminación.',
        inputs: [{ name: 'password', type: 'password', placeholder: 'Contraseña' }],
        buttons: [
          { text: 'Cancelar', role: 'cancel', handler: () => resolve(false) },
          {
            text: 'Confirmar',
            handler: async (data) => {
              const valido = !!data.password && await this.auth.verifyPassword(data.password);
              if (!valido) {
                await this.mostrarError();
                resolve(false);
              } else {
                resolve(true);
              }
            },
          },
        ],
      }).then(a => a.present());
    });
  }

  private async mostrarError(): Promise<void> {
    const alert = await this.alertCtrl.create({
      header: 'Contraseña incorrecta',
      message: 'No pudimos verificar tu contraseña. Intentá de nuevo.',
      buttons: ['OK'],
    });
    await alert.present();
  }
}
