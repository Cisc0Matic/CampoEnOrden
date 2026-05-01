import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of, BehaviorSubject, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from 'src/environments/environment';

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

  constructor(private http: HttpClient) {
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

  get<T>(path: string): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}/${path}`, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        console.warn('API error:', error);
        return of(null as T);
      })
    );
  }

  post<T>(path: string, body: object): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}/${path}`, body, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('POST', path, body);
        return of({ success: true, offline: true } as T);
      })
    );
  }

  put<T>(path: string, body: object): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}/${path}`, body, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('PUT', path, body);
        return of({ success: true, offline: true } as T);
      })
    );
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}/${path}`, { headers: this.getHeaders() }).pipe(
      catchError((error) => {
        this.queueRequest('DELETE', path);
        return of({ success: true, offline: true } as T);
      })
    );
  }

  get isOnline(): boolean {
    return navigator.onLine;
  }

  get pendingCount(): number {
    return this.pendingRequests.length;
  }
}