import { Injectable } from '@angular/core';
import { CanLoad, Route, UrlSegment, UrlTree, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { Storage } from '@ionic/storage-angular';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanLoad {

  constructor(private storage: Storage, private router: Router) {}

  async canLoad(
    route: Route,
    segments: UrlSegment[]): Promise<boolean | UrlTree> {
    console.log('AuthGuard: Checking authentication...');
    await this.storage.create(); // Ensure storage is ready
    const token = await this.storage.get('jwt_token');

    if (token) {
      console.log('AuthGuard: Token found, allowing access.');
      return true; // User is authenticated
    } else {
      console.log('AuthGuard: No token found, redirecting to login.');
      return this.router.parseUrl('/login');
    }
  }
}
