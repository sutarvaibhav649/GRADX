import { Routes } from "@angular/router";
import { FacultyDashboardComponent } from "./faculty-dashboard/faculty-dashboard.component";
import { authGuard } from "../shared/guards/auth-guard.guard";
import { ProfileComponent } from "../shared/profile/profile.component";

export const facultyRoutes: Routes = [
  {
    path: 'dashboard',
    component: FacultyDashboardComponent,
    canActivate: [authGuard],
    data: { role: 'faculty' }
  },
  {
    path: 'profile',
    component: ProfileComponent,
    canActivate: [authGuard],
    data: { role: 'faculty' }
  }
];
