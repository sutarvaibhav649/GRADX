import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isLoggedIn()) {
    router.navigate(['/auth/login']);
    return false;
  }

  const requiredRole: string = route.data?.['role'];
  if (requiredRole && auth.getUser()?.role !== requiredRole) {
    const userRole = auth.getUser()?.role;
    router.navigate([`/${userRole}/dashboard`]);
    return false;
  }

  return true;
};
