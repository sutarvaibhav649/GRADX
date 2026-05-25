import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ToastService } from '../toast.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = environment.apiUrl;
  private userSubject = new BehaviorSubject<any>(this.loadUser());
  currentUser$ = this.userSubject.asObservable();

  constructor(private http: HttpClient, private toastService: ToastService) {}

  private loadUser() {
    try {
      if (typeof localStorage === 'undefined') return null;
      const u = localStorage.getItem('gradx_user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      this.toastService.show('error', 'Failed to load user data. Please login again.');
      console.warn('Failed to load user from localStorage', e);
      localStorage.removeItem('gradx_user');
      localStorage.removeItem('gradx_token');
      return null;
    }
  }

  login(email: string, password: string, role: string) {
    return this.http.post<any>(`${this.api}/auth/login`, { email, password, role }).pipe(
      tap(res => {
        localStorage.setItem('gradx_token', res.token);
        localStorage.setItem('gradx_user', JSON.stringify(res.user));
        this.userSubject.next(res.user);
      })
    );
  }

  signup(data: any) {
    return this.http.post<any>(`${this.api}/auth/signup`, data).pipe(
      tap(res => {
        localStorage.setItem('gradx_token', res.token);
        localStorage.setItem('gradx_user', JSON.stringify(res.user));
        this.userSubject.next(res.user);
      })
    );
  }

  logout() {
    localStorage.removeItem('gradx_token');
    localStorage.removeItem('gradx_user');
    this.toastService.show('info', 'Logged out successfully.');
    this.userSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem('gradx_token');
  }

  getUser(): any {
    return this.userSubject.value;
  }

  isLoggedIn(): boolean {
    const token = this.getToken();
    if (!token) return false;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.exp && Date.now() / 1000 > payload.exp) {
        this.logout();
        return false;
      }
    } catch {
      return false;
    }
    return true;
  }

  getMe() {
    return this.http.get<any>(`${this.api}/auth/me`);
  }

  updateProfile(data: any) {
    return this.http.put<any>(`${this.api}/auth/profile`, data).pipe(
      tap(res => {
        const user = res.user || res.data;
        if (user) {
          localStorage.setItem('gradx_user', JSON.stringify(user));
          this.userSubject.next(user);
        }
      })
    );
  }

  changePassword(currentPassword: string, newPassword: string) {
    return this.http.put<any>(`${this.api}/auth/change-password`, { currentPassword, newPassword });
  }
}
