import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError } from 'rxjs/internal/operators/catchError';
import { ToastService } from '../toast.service';
import { throwError } from 'rxjs';
import { Router } from '@angular/router';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toastService = inject(ToastService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unknown error occurred!';

      if (error.status === 0) {
        errorMessage = 'Cannot reach server. Please check your connection.';
      } else if (error.status === 401) {
        localStorage.removeItem('gradx_token');
        localStorage.removeItem('gradx_user');
        toastService.show('warn', 'Session expired. Please log in again.');
        router.navigate(['/auth/login']);
        return throwError(() => error);
      } else if (error.status === 409) {
        errorMessage = error.error?.message || 'Resource conflict occurred.';
      } else if (error.status === 422) {
        if (error.error?.errors?.length) {
          errorMessage = error.error.errors.map((e: any) => e.msg).join(', ');
        } else {
          errorMessage = error.error?.message || 'Validation failed.';
        }
      } else if (error.status >= 400 && error.status < 500) {
        errorMessage = error.error?.message || error.statusText || 'Request failed.';
      } else if (error.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      }

      toastService.show('warn', errorMessage);
      return throwError(() => error);
    })
  );
};
