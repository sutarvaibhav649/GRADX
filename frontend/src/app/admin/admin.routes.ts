import { Routes } from "@angular/router";
import { AdminDashboardComponent } from "./admin-dashboard/admin-dashboard.component";
import { authGuard } from "../shared/guards/auth-guard.guard";
import { ProfileComponent } from "../shared/profile/profile.component";
import { UserManagementComponent } from "./user-management/user-management.component";

export const adminRoutes: Routes = [
  {
    path: 'dashboard',
    component: AdminDashboardComponent,
    canActivate: [authGuard],
    data: { role: 'admin' }
  },
  {
    path: 'profile',
    component: ProfileComponent,
    canActivate: [authGuard],
    data: { role: 'admin' }
  },
  {
    path: 'users',
    component: UserManagementComponent,
    canActivate: [authGuard],
    data: { role: 'admin' }
  }
];
