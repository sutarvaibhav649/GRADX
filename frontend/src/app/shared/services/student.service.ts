import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class StudentService {
  private api = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getDashboard() {
    return this.http.get<any>(`${this.api}/student/dashboard`);
  }

  getMyResults(params: any = {}) {
    return this.http.get<any>(`${this.api}/student/results`, { params });
  }

  getResultById(id: string) {
    return this.http.get<any>(`${this.api}/student/results/${id}`);
  }
}
