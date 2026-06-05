import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NavController } from '@ionic/angular';
import { Storage } from '@ionic/storage-angular';
import { firstValueFrom } from 'rxjs';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  role_display: string;
  telefono: string | null;
  empresa: number | null;
  empresa_nombre: string | null;
  is_active: boolean;
}

export interface RegisterData {
  empresa_nombre: string;
  username: string;
  email: string;
  first_name: string;
  last_name?: string;
  password: string;
  password_confirm: string;
}

export interface AcceptInviteData {
  token: string;
  username: string;
  first_name: string;
  last_name?: string;
  password: string;
  password_confirm: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly API = '/api/users';
  private _currentUser: UserProfile | null = null;

  constructor(
    private http: HttpClient,
    private storage: Storage,
    private navCtrl: NavController,
  ) {}

  async init(): Promise<void> {
    await this.storage.create();
  }

  async getToken(): Promise<string | null> {
    return localStorage.getItem('jwt_token') || await this.storage.get('jwt_token');
  }

  async isLoggedIn(): Promise<boolean> {
    return !!(await this.getToken());
  }

  async getCurrentUser(): Promise<UserProfile | null> {
    if (this._currentUser) return this._currentUser;
    const cached = await this.storage.get('current_user');
    if (cached) {
      this._currentUser = cached;
      return cached;
    }
    try {
      const user = await firstValueFrom(
        this.http.get<UserProfile>(`${this.API}/auth/me/`)
      );
      this._currentUser = user;
      await this.storage.set('current_user', user);
      return user;
    } catch {
      return null;
    }
  }

  hasRole(...roles: string[]): boolean {
    return !!this._currentUser && roles.includes(this._currentUser.role);
  }

  isAdmin(): boolean {
    return this.hasRole('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA');
  }

  // ─── Flujos de autenticación ───────────────────────────────────────────────

  async login(username: string, password: string): Promise<void> {
    const res = await firstValueFrom(
      this.http.post<{ access: string; refresh: string }>('/api/token/', { username, password })
    );
    await this._saveSession(res.access, res.refresh, username);
  }

  async logout(): Promise<void> {
    try {
      const refresh = await this.storage.get('refresh_token');
      if (refresh) {
        await firstValueFrom(
          this.http.post(`${this.API}/auth/logout/`, { refresh })
        );
      }
    } catch {}
    await this._clearSession();
    this.navCtrl.navigateRoot('/login');
  }

  async register(data: RegisterData): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/auth/register/`, data));
  }

  async activateAccount(token: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/auth/activate/`, { token }));
  }

  async resendActivation(email: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/auth/resend-activation/`, { email }));
  }

  async resendActivationByUsername(username: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/auth/resend-activation/`, { username }));
  }

  async requestPasswordReset(email: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/auth/password-reset/`, { email }));
  }

  async confirmPasswordReset(token: string, password: string, passwordConfirm: string): Promise<void> {
    await firstValueFrom(
      this.http.post(`${this.API}/auth/password-reset/confirm/`, {
        token,
        password,
        password_confirm: passwordConfirm,
      })
    );
  }

  // ─── Invitaciones ─────────────────────────────────────────────────────────

  async getInvitationInfo(token: string): Promise<{ email: string; role_display: string; empresa: string }> {
    return firstValueFrom(
      this.http.get<any>(`${this.API}/invite/accept/?token=${token}`)
    );
  }

  async acceptInvitation(data: AcceptInviteData): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/invite/accept/`, data));
  }

  // ─── Gestión de usuarios (admin) ──────────────────────────────────────────

  async inviteUser(email: string, role: string): Promise<void> {
    await firstValueFrom(this.http.post(`${this.API}/invite/`, { email, role }));
  }

  async createUser(data: any): Promise<UserProfile> {
    return firstValueFrom(this.http.post<UserProfile>(`${this.API}/create/`, data));
  }

  async listUsers(): Promise<UserProfile[]> {
    return firstValueFrom(this.http.get<UserProfile[]>(`${this.API}/list/`));
  }

  async adminResetPassword(userId: number, newPassword: string): Promise<void> {
    await firstValueFrom(
      this.http.post(`${this.API}/${userId}/reset-password/`, { new_password: newPassword })
    );
  }

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const updated = await firstValueFrom(
      this.http.patch<UserProfile>(`${this.API}/auth/me/`, data)
    );
    this._currentUser = updated;
    await this.storage.set('current_user', updated);
    return updated;
  }

  // ─── Privados ─────────────────────────────────────────────────────────────

  private async _saveSession(access: string, refresh: string, username: string): Promise<void> {
    localStorage.setItem('jwt_token', access);
    await this.storage.set('jwt_token', access);
    await this.storage.set('refresh_token', refresh);
    await this.storage.set('username', username);
    this._currentUser = null;
  }

  private async _clearSession(): Promise<void> {
    localStorage.removeItem('jwt_token');
    await this.storage.remove('jwt_token');
    await this.storage.remove('refresh_token');
    await this.storage.remove('username');
    await this.storage.remove('current_user');
    this._currentUser = null;
  }
}
