import { Routes } from "@angular/router";
import { AdminDashboardComponent } from "./admin-dashboard/admin-dashboard.component";
import { authGuard } from "../shared/guards/auth-guard.guard";

export const adminRoutes: Routes = [
  {
    path: 'dashboard',
    component: AdminDashboardComponent,
    canActivate: [authGuard],
    data: { role: 'admin' }
  }
];
