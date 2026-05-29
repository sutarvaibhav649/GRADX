import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private api = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getDashboard() {
    return this.http.get<any>(`${this.api}/admin/dashboard`);
  }

  getAllUsers(params: any = {}) {
    return this.http.get<any>(`${this.api}/admin/users`, { params });
  }

  getUserById(id: string) {
    return this.http.get<any>(`${this.api}/admin/users/${id}`);
  }

  createUser(data: any) {
    return this.http.post<any>(`${this.api}/admin/users`, data);
  }

  updateUser(id: string, data: any) {
    return this.http.put<any>(`${this.api}/admin/users/${id}`, data);
  }

  deleteUser(id: string) {
    return this.http.delete<any>(`${this.api}/admin/users/${id}`);
  }

  getAllExams(params: any = {}) {
    return this.http.get<any>(`${this.api}/admin/exams`, { params });
  }

  getAllResults(params: any = {}) {
    return this.http.get<any>(`${this.api}/admin/results`, { params });
  }
}
