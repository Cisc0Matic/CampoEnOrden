import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, of, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { DataStoreService } from './data-store.service';

interface PendingRequest {
  method: string;
  path: string;
  body?: object;
  id: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;
  private pendingRequests: PendingRequest[] = [];
  private syncInProgress = new BehaviorSubject<boolean>(false);
  private storage: any = null;

  constructor(private http: HttpClient, private dataStore: DataStoreService) {
    this.loadPendingRequests();
    this.setupAutoSync();
  }

  setStorage(storage: Storage) {
    this.storage = storage;
    this.loadPendingRequests();
  }

  private async loadPendingRequests() {
    if (!this.storage) return;
    try {
      const saved = await this.storage.get('pending_requests');
      if (saved) {
        this.pendingRequests = JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Error loading pending requests:', e);
    }
  }

  private async savePendingRequests() {
    if (!this.storage) return;
    try {
      await this.storage.set('pending_requests', JSON.stringify(this.pendingRequests));
    } catch (e) {
      console.warn('Error saving pending requests:', e);
    }
  }

  private setupAutoSync() {
    window.addEventListener('online', () => {
      if (this.pendingRequests.length > 0) {
        this.syncPendingRequests();
      }
    });
  }

  async syncPendingRequests() {
    if (this.syncInProgress.value || this.pendingRequests.length === 0 || !navigator.onLine) return;
    
    this.syncInProgress.next(true);
    
    while (this.pendingRequests.length > 0) {
      const request = this.pendingRequests[0];
      try {
        await this.executeRequest(request).toPromise();
        this.pendingRequests.shift();
        await this.savePendingRequests();
      } catch (error) {
        break;
      }
    }
    
    this.syncInProgress.next(false);
  }

  private executeRequest(req: PendingRequest): Observable<any> {
    switch (req.method) {
      case 'GET': return this.http.get(`${this.baseUrl}/${req.path}`, { headers: this.getHeaders() });
      case 'POST': return this.http.post(`${this.baseUrl}/${req.path}`, req.body, { headers: this.getHeaders() });
      case 'PUT': return this.http.put(`${this.baseUrl}/${req.path}`, req.body, { headers: this.getHeaders() });
      case 'DELETE': return this.http.delete(`${this.baseUrl}/${req.path}`, { headers: this.getHeaders() });
      default: return throwError(() => new Error('Unknown method'));
    }
  }

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  private async queueRequest(method: string, path: string, body?: object) {
    const id = `${Date.now()}-${Math.random()}`;
    const pendingRequest: PendingRequest = { method, path, body, id };
    this.pendingRequests.push(pendingRequest);
    await this.savePendingRequests();
  }

  get<T>(path: string, options?: { params?: HttpParams | { [param: string]: string | string[] } }): Observable<T> {
    const key = this.cacheKey(path, options?.params);
    return this.dataStore.stream(key, () => this.fetchGet<T>(path, options)) as unknown as Observable<T>;
  }

  private fetchGet<T>(path: string, options?: { params?: HttpParams | { [param: string]: string | string[] } }): Observable<T> {
    const httpOptions: any = { headers: this.getHeaders() };
    if (options?.params) {
      httpOptions.params = options.params;
    }
    return this.http.get<T>(`${this.baseUrl}/${path}`, httpOptions).pipe(
      catchError((error) => {
        console.warn('API error:', error);
        return of(null as any);
      })
    );
  }

  post<T>(path: string, body: any): Observable<T> {
    // Handle FormData for file uploads
    if (body instanceof FormData) {
      const headers = this.getHeaders();
      headers.delete('Content-Type'); // Let browser set it for FormData
      return this.http.post<T>(`${this.baseUrl}/${path}`, body, { headers }).pipe(
        catchError((error) => {
          this.queueRequest('POST', path, body);
          return of({ success: true, offline: true } as T);
        }),
        tap((res) => { if (!this.isOfflineResult(res)) this.invalidateForWrite(path); })
      );
    }
    
    return this.http.post<T>(`${this.baseUrl}/${path}`, body, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('POST', path, body);
        return of({ success: true, offline: true } as T);
      }),
      tap((res) => { if (!this.isOfflineResult(res)) this.invalidateForWrite(path); })
    );
  }

  put<T>(path: string, body: any): Observable<T> {
    // Handle FormData for file uploads
    if (body instanceof FormData) {
      const headers = this.getHeaders();
      headers.delete('Content-Type'); // Let browser set it for FormData
      return this.http.put<T>(`${this.baseUrl}/${path}`, body, { headers }).pipe(
        catchError((error) => {
          this.queueRequest('PUT', path, body);
          return of({ success: true, offline: true } as T);
        }),
        tap((res) => { if (!this.isOfflineResult(res)) this.invalidateForWrite(path); })
      );
    }
    
    return this.http.put<T>(`${this.baseUrl}/${path}`, body, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('PUT', path, body);
        return of({ success: true, offline: true } as T);
      }),
      tap((res) => { if (!this.isOfflineResult(res)) this.invalidateForWrite(path); })
    );
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}/${path}`, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('DELETE', path);
        return of({ success: true, offline: true } as T);
      }),
      tap((res) => { if (!this.isOfflineResult(res)) this.invalidateForWrite(path); })
    );
  }

  private cacheKey(path: string, params?: HttpParams | { [param: string]: string | string[] }): string {
    if (!params) return path;
    if (params instanceof HttpParams) return `${path}?${params.toString()}`;
    try {
      const sorted: { [key: string]: string | string[] } = {};
      for (const key of Object.keys(params).sort()) {
        sorted[key] = params[key];
      }
      return `${path}?${JSON.stringify(sorted)}`;
    } catch {
      return path;
    }
  }

  private isOfflineResult(res: any): boolean {
    return !!res && res.offline === true;
  }

  private invalidateForWrite(path: string): void {
    const segments = path.split('/').filter(Boolean);
    const coreIdx = segments.indexOf('core');
    const resource = coreIdx >= 0 && segments[coreIdx + 1] ? segments[coreIdx + 1] : null;
    if (resource) {
      this.dataStore.invalidatePrefix(`core/${resource}`);
    }
    this.dataStore.invalidatePrefix('core/dashboard');
    this.dataStore.invalidatePrefix('core/campos');
  }

  get isOnline(): boolean {
    return navigator.onLine;
  }

  get pendingCount(): number {
    return this.pendingRequests.length;
  }
}