import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { from, Observable } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';
import { tokenStore, setToken } from '../services/token-store';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isStorageReady = false;
  private tokenLoaded = false;

  constructor(private storage: Storage, private router: Router) {}

  private async getReadyStorage() {
    if (!this.isStorageReady) {
      await this.storage.create();
      this.isStorageReady = true;
    }
    return this.storage;
  }

  private async ensureToken(): Promise<string | null> {
    if (tokenStore.token !== null) {
      return tokenStore.token;
    }
    if (this.tokenLoaded) {
      return null;
    }
    await this.getReadyStorage();
    const token = (await this.storage.get('jwt_token')) || null;
    tokenStore.token = token;
    this.tokenLoaded = true;
    if (token) {
      localStorage.setItem('jwt_token', token);
    }
    return token;
  }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return from(this.ensureToken()).pipe(
      switchMap(token => {
        if (token) {
          const authReq = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          return next.handle(authReq).pipe(
            tap({
              error: (error: HttpErrorResponse) => {
                this.tokenLoaded = false;
                if (error.status === 401) {
                  setToken(null);
                  this.storage.remove('jwt_token');
                  this.router.navigate(['/login']);
                }
              }
            })
          );
        } else {
          return next.handle(request);
        }
      })
    );
  }
}