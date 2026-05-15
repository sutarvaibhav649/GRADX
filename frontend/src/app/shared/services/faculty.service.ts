import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class FacultyService {
  private api = environment.apiUrl;
  

  constructor(private http: HttpClient) {}

  getDashboard() {
    return this.http.get<any>(`${this.api}/faculty/dashboard`);
  }


  createExam(formData: FormData) {
    return this.http.post<any>(`${this.api}/faculty/exams`, formData);
  }

  getMyExams(params: any = {}) {
    return this.http.get<any>(`${this.api}/faculty/exams`, { params });
  }

  getExamById(id: string) {
    return this.http.get<any>(`${this.api}/faculty/exams/${id}`);
  }

  deleteExam(id: string) {
    return this.http.delete<any>(`${this.api}/faculty/exams/${id}`);
  }

  startEvaluation(examId: string) {
    return this.http.post<any>(`${this.api}/evaluation/start/${examId}`, {});
  }

  getExamResults(examId: string) {
    return this.http.get<any>(`${this.api}/faculty/exams/${examId}/results`);
  }

  finalizeResult(examId:string) {
    return this.http.put<any>(`${this.api}/evaluation/results/${examId}/finalize`,{});
  }

  getResultByExamId(examId: string) {
    return this.http.get<any>(`${this.api}/evaluation/results/${examId}`);
  }

  updateEvaluationResult(resultId: string, data: any) {
  return this.http.put<any>(`${this.api}/evaluation/results/${resultId}`, data);
}

getEvaluationResultsWithDetails(examId: string) {
    return this.http.get<any>(`${this.api}/faculty/exams/${examId}/results`);
}
}
