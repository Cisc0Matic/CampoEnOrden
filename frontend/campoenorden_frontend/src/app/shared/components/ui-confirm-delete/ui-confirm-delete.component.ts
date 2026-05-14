import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'ui-confirm-delete',
  template: '',
  standalone: true,
  imports: [CommonModule],
})
export class UiConfirmDeleteComponent {
  @Input() itemName = 'este elemento';
  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  constructor(private alertCtrl: AlertController) {}

  async present() {
    const alert = await this.alertCtrl.create({
      header: 'Confirmar eliminación',
      message: `¿Estás seguro de que deseas eliminar ${this.itemName}? Esta acción no se puede deshacer.`,
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel',
          handler: () => this.cancel.emit(),
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => this.confirm.emit(),
        },
      ],
    });
    await alert.present();
  }
}
