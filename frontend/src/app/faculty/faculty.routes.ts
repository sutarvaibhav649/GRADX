import { Routes } from "@angular/router";
import { FacultyDashboardComponent } from "./faculty-dashboard/faculty-dashboard.component";
import { authGuard } from "../shared/guards/auth-guard.guard";

export const facultyRoutes: Routes = [
  {
    path: 'dashboard',
    component: FacultyDashboardComponent,
    canActivate: [authGuard],
    data: { role: 'faculty' }
  }
];
