import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { from, Observable } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';
import { Storage } from '@ionic/storage-angular';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isStorageReady = false;

  constructor(private storage: Storage) {
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
    // 1. Logs para ver qué URL se está intentando consultar
    console.log(`Interceptor: Capturando petición a -> ${request.url}`);

    return from(this.getReadyStorage()).pipe(
      // 2. Intentamos obtener el token
      switchMap(storage => from(storage.get('jwt_token'))),
      switchMap(token => {
        if (token) {
          console.log('Interceptor: Token encontrado en Storage. Clonando headers...');
          
          // Clonamos la petición e inyectamos el token
          const authReq = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          
          console.log('Interceptor: Header Authorization inyectado con éxito.');
          return next.handle(authReq);
        } else {
          // 3. Alerta si no hay token
          console.warn('Interceptor: No se encontró jwt_token en el Storage. La petición saldrá sin auth.');
          return next.handle(request);
        }
      })
    );
  }
}