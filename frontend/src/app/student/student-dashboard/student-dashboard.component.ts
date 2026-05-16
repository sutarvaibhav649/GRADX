import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { UpperCasePipe, CommonModule, DecimalPipe } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { StudentService } from '../../shared/services/student.service';
import { ToastService } from '../../shared/toast.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-student-dashboard',
  imports: [UpperCasePipe, CommonModule, DecimalPipe],
  templateUrl: './student-dashboard.component.html',
  styleUrl: './student-dashboard.component.css',
})
export class StudentDashboardComponent implements OnInit {
  stats = { totalEvaluated: 0, averageScore: 0, topPerformances: 0, pendingResults: 0 };
  results: any[] = [];

  showDetailModal = false;
  selectedResult: any = null;
  loadingDetail = false;

  get userInitial() { return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'S'; }
  get userName() { return this.auth.getUser()?.fullName || 'Student'; }

  constructor(
    private auth: AuthService,
    private studentService: StudentService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnInit() {
    this.loadDashboard();
  }

  loadDashboard() {
    this.studentService.getDashboard().subscribe({
      next: (res) => {
        this.stats = res.data.stats;
        this.results = res.data.recentResults;
        this.toastService.show('success', 'Student dashboard loaded.');
      },
      error: () => {}
    });
  }

  viewDetail(resultId: string) {
    this.loadingDetail = true;
    this.showDetailModal = true;
    this.selectedResult = null;

    this.studentService.getResultById(resultId).subscribe({
      next: (res) => {
        this.selectedResult = res.data;
        this.loadingDetail = false;
      },
      error: () => {
        this.loadingDetail = false;
        this.toastService.show('error', 'Could not load result details.');
        this.showDetailModal = false;
      }
    });
  }

  closeDetailModal() {
    this.showDetailModal = false;
    this.selectedResult = null;
  }

  get sectionScores(): { name: string; earned: number; max: number; pct: number }[] {
    const scores = this.selectedResult?.aiEvaluationDetails?.section_scores;
    if (!scores) return [];
    return Object.entries(scores).map(([name, data]: [string, any]) => ({
      name,
      earned: data.marks_awarded ?? 0,
      max: data.max_marks ?? 0,
      pct: data.percentage ?? 0
    }));
  }

  get feedback() {
    return this.selectedResult?.aiEvaluationDetails?.feedback || null;
  }

  get gradeColor(): string {
    const g = this.selectedResult?.grade;
    const map: Record<string, string> = {
      'O': '#28a745', 'A+': '#20c997', 'A': '#17a2b8',
      'B+': '#6f42c1', 'B': '#fd7e14', 'C': '#ffc107', 'F': '#dc3545'
    };
    return map[g] || '#6c757d';
  }

  get studentImageUrl(): string {
    const filePath = this.selectedResult?.studentAnswerSheet?.filePath || '';
    if (!filePath) return '';
    const base = environment.apiUrl.replace('/api', '');
    return `${base}${filePath}`;
  }

  get lowConfidence(): boolean {
    return this.selectedResult?.aiEvaluationDetails?.low_confidence === true;
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }
}
