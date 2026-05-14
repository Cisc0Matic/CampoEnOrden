import { Component } from '@angular/core';
import { Storage } from '@ionic/storage-angular';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent {
  constructor(private storage: Storage) {
    this.initStorage();
  }

  private async initStorage() {
    await this.storage.create();
    const token = await this.storage.get('jwt_token');
    if (token && !localStorage.getItem('jwt_token')) {
      localStorage.setItem('jwt_token', token);
    }
  }
}
