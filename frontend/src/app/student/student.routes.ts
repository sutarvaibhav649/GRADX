import { Routes } from "@angular/router";
import { StudentDashboardComponent } from "./student-dashboard/student-dashboard.component";
import { authGuard } from "../shared/guards/auth-guard.guard";

export const studentRoutes: Routes = [
  {
    path: 'dashboard',
    component: StudentDashboardComponent,
    canActivate: [authGuard],
    data: { role: 'student' }
  }
];
