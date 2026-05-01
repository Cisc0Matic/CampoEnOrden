import { Injectable } from '@angular/core';
import { CanLoad, CanActivate, Route, UrlSegment, UrlTree, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { Storage } from '@ionic/storage-angular';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanLoad, CanActivate {

  constructor(private storage: Storage, private router: Router) {}

  private async checkAuth(): Promise<boolean | UrlTree> {
    console.log('AuthGuard: Checking authentication...');
    await this.storage.create();
    const token = localStorage.getItem('jwt_token') || await this.storage.get('jwt_token');

    if (token) {
      console.log('AuthGuard: Token found, allowing access.');
      return true;
    } else {
      console.log('AuthGuard: No token found, redirecting to login.');
      return this.router.parseUrl('/login');
    }
  }

  async canLoad(route: Route, segments: UrlSegment[]): Promise<boolean | UrlTree> {
    return this.checkAuth();
  }

  async canActivate(): Promise<boolean | UrlTree> {
    return this.checkAuth();
  }
}
