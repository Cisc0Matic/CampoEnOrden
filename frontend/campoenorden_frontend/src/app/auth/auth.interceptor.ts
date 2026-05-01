import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { from, Observable, throwError } from 'rxjs';
import { switchMap, tap, catchError } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isStorageReady = false;

  constructor(private storage: Storage, private router: Router) {
    console.log('Interceptor: Constructor inicializado');
  }

  private async getReadyStorage() {
    if (!this.isStorageReady) {
      console.log('Interceptor: Inicializando base de datos de Storage...');
      await this.storage.create();
      this.isStorageReady = true;
      console.log('Interceptor: Storage listo.');
    }
    return this.storage;
  }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    console.log(`Interceptor: Capturando petición a -> ${request.url}`);

    return from(this.getReadyStorage()).pipe(
      switchMap(storage => from(storage.get('jwt_token'))),
      switchMap(token => {
        if (token) {
          console.log('Interceptor: Token encontrado en Storage. Clonando headers...');
          
          const authReq = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          
          console.log('Interceptor: Header Authorization inyectado con éxito.');
          return next.handle(authReq).pipe(
            catchError((error: HttpErrorResponse) => {
              if (error.status === 401) {
                console.warn('Interceptor: Error 401 - Token inválido o expirado. Redirigiendo a login...');
                this.storage.remove('jwt_token');
                this.router.navigate(['/login']);
                return throwError(() => error);
              }
              return throwError(() => error);
            })
          );
        } else {
          console.warn('Interceptor: No se encontró jwt_token en el Storage. La petición saldrá sin auth.');
          return next.handle(request);
        }
      })
    );
  }
}