import { Injectable } from '@angular/core';
import { NavController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  constructor(private storage: Storage, private navCtrl: NavController) {}

  async logout() {
    await this.storage.remove('jwt_token');
    await this.navCtrl.navigateRoot('/login');
  }

  async isLoggedIn(): Promise<boolean> {
    const token = await this.storage.get('jwt_token');
    return !!token;
  }
}
