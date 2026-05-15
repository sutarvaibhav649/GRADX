import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { UpperCasePipe } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { AdminService } from '../../shared/services/admin.service';
import { ToastService } from '../../shared/toast.service';

@Component({
  selector: 'app-admin-dashboard',
  imports: [UpperCasePipe],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css',
})
export class AdminDashboardComponent implements OnInit {
  stats = {
    totalUsers: 0,
    totalStudents: 0,
    totalFaculty: 0,
    totalExams: 0,
    completedEvals: 0,
    averageScore: 0,
    systemAccuracy: 0
  };
  recentExams: any[] = [];

  get userInitial() { return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'A'; }
  get userName() { return this.auth.getUser()?.fullName || 'Admin'; }

  constructor(
    private auth: AuthService,
    private adminService: AdminService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnInit() {
    this.loadDashboard();
  }

  loadDashboard() {
    this.adminService.getDashboard().subscribe({
      next: (res) => {
        this.stats = res.data.stats;
        this.recentExams = res.data.recentExams;
        this.toastService.show('success', 'Dashboard data loaded successfully.');
      },
      error: (err:any) => {
        console.error('Error loading dashboard:', err);
      }
    });
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }
}
