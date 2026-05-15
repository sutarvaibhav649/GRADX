import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { UpperCasePipe } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { StudentService } from '../../shared/services/student.service';
import { ToastService } from '../../shared/toast.service';

@Component({
  selector: 'app-student-dashboard',
  imports: [UpperCasePipe],
  templateUrl: './student-dashboard.component.html',
  styleUrl: './student-dashboard.component.css',
})
export class StudentDashboardComponent implements OnInit {
  stats = { totalEvaluated: 0, averageScore: 0, topPerformances: 0, pendingResults: 0 };
  results: any[] = [];

  get userInitial() { return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'S'; }
  get userName() { return this.auth.getUser()?.fullName || 'Student'; }

  constructor(
    private auth: AuthService,
    private studentService: StudentService,
    private router: Router,
    private toastService:ToastService
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

  logout() {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }
}
