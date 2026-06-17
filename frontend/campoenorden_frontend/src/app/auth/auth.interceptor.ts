import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { from, Observable, throwError } from 'rxjs';
import { switchMap, tap, catchError } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isStorageReady = false;

  constructor(private storage: Storage, private router: Router) {}

  private async getReadyStorage() {
    if (!this.isStorageReady) {
      await this.storage.create();
      this.isStorageReady = true;
    }
    return this.storage;
  }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return from(this.getReadyStorage()).pipe(
      switchMap(storage => from(storage.get('jwt_token'))),
      switchMap(token => {
        if (token) {
          const authReq = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          return next.handle(authReq).pipe(
            catchError((error: HttpErrorResponse) => {
              if (error.status === 401) {
                this.storage.remove('jwt_token');
                this.router.navigate(['/login']);
                return throwError(() => error);
              }
              return throwError(() => error);
            })
          );
        } else {
          return next.handle(request);
        }
      })
    );
  }
}