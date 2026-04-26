import { Injectable, NgZone } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ConnectivityService {
  private connected$ = new BehaviorSubject<boolean>(navigator.onLine);

  constructor(private ngZone: NgZone) {
    this.initNetworkListener();
  }

  get isConnected(): Observable<boolean> {
    return this.connected$.asObservable();
  }

  get currentStatus(): boolean {
    return this.connected$.value;
  }

  private initNetworkListener() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.ngZone.run(() => {
          this.connected$.next(true);
        });
      });
      window.addEventListener('offline', () => {
        this.ngZone.run(() => {
          this.connected$.next(false);
        });
      });
    }
  }

  async checkConnection(): Promise<boolean> {
    return navigator.onLine;
  }
}