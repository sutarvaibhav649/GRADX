import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { UpperCasePipe, CommonModule, DecimalPipe } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { StudentService } from '../../shared/services/student.service';
import { ToastService } from '../../shared/toast.service';
import { environment } from '../../../environments/environment';
import { Subscription, finalize, timeout } from 'rxjs';
import { DomSanitizer, SafeResourceUrl, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-student-dashboard',
  imports: [UpperCasePipe, CommonModule, DecimalPipe, RouterLink],
  templateUrl: './student-dashboard.component.html',
  styleUrl: './student-dashboard.component.css',
})
export class StudentDashboardComponent implements OnInit, OnDestroy {
  stats = { totalEvaluated: 0, averageScore: 0, topPerformances: 0, pendingResults: 0 };
  results: any[] = [];

  showDetailModal = false;
  selectedResult: any = null;
  loadingDetail = false;
  isLoadingDashboard = false;
  private dashboardRefreshInterval?: ReturnType<typeof setInterval>;
  private dashboardSub?: Subscription;
  private detailSub?: Subscription;
  private readonly handleWindowFocus = () => this.loadDashboard(false);

  get userInitial() { return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'S'; }
  get userName() { return this.auth.getUser()?.fullName || 'Student'; }

  constructor(
    private auth: AuthService,
    private studentService: StudentService,
    private router: Router,
    private toastService: ToastService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadDashboard();
    window.addEventListener('focus', this.handleWindowFocus);
    this.dashboardRefreshInterval = setInterval(() => this.loadDashboard(false), 15000);
  }

  ngOnDestroy() {
    this.dashboardSub?.unsubscribe();
    this.detailSub?.unsubscribe();
    window.removeEventListener('focus', this.handleWindowFocus);
    if (this.dashboardRefreshInterval) {
      clearInterval(this.dashboardRefreshInterval);
    }
  }

  loadDashboard(showError = true) {
    if (this.isLoadingDashboard) {
      return;
    }

    this.isLoadingDashboard = true;
    this.dashboardSub = this.studentService.getDashboard()
      .pipe(finalize(() => {
        this.isLoadingDashboard = false;
        this.cdr.markForCheck();
      }))
      .subscribe({
      next: (res) => {
        this.stats = res.data?.stats || this.stats;
        this.results = res.data?.recentResults || [];
        this.cdr.markForCheck();
      },
      error: () => {
        if (showError) {
          this.toastService.show('error', 'Failed to load dashboard. Please refresh.');
        }
        this.cdr.markForCheck();
      }
    });
  }

  viewDetail(result: any) {
    this.loadingDetail = true;
    this.showDetailModal = true;
    this.selectedResult = result;

    this.detailSub?.unsubscribe();
    this.detailSub = this.studentService.getResultById(result._id)
      .pipe(
        timeout(15000),
        finalize(() => {
          this.loadingDetail = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
      next: (res) => {
        this.selectedResult = res.data || result;
        this.cdr.markForCheck();
      },
      error: () => {
        this.toastService.show('error', 'Could not load result details.');
        this.cdr.markForCheck();
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

  get studentAnswerSheetUrl(): string {
    const filePath = this.selectedResult?.studentAnswerSheet?.filePath || '';
    if (!filePath) return '';
    return this.toFileUrl(filePath);
  }

  get isStudentAnswerSheetPdf(): boolean {
    const sheet = this.selectedResult?.studentAnswerSheet;
    const fileName = `${sheet?.originalName || ''} ${sheet?.filePath || ''}`.toLowerCase();
    return fileName.includes('.pdf');
  }

  get studentAnswerSheetPdfUrl(): SafeResourceUrl | null {
    if (!this.studentAnswerSheetUrl) return null;
    return this.sanitizer.bypassSecurityTrustResourceUrl(this.studentAnswerSheetUrl);
  }

  get studentAnswerSheetOpenUrl(): SafeUrl | null {
    if (!this.studentAnswerSheetUrl) return null;
    return this.sanitizer.bypassSecurityTrustUrl(this.studentAnswerSheetUrl);
  }

  private toFileUrl(filePath: string): string {
    const normalizedPath = String(filePath).replace(/\\/g, '/').trim();

    if (!normalizedPath) {
      return '';
    }

    if (/^(https?:)?\/\//i.test(normalizedPath)) {
      return normalizedPath;
    }

    const backendBase = (environment.backendUrl || '').replace(/\/$/, '');
    const pathWithSlash = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`;
    return `${backendBase}${pathWithSlash}`;
  }

  get lowConfidence(): boolean {
    return this.selectedResult?.aiEvaluationDetails?.low_confidence === true;
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }
}
