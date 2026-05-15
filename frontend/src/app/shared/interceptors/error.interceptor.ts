import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError } from 'rxjs/internal/operators/catchError';
import { ToastService } from '../toast.service';
import { throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {

  const toastService = inject(ToastService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unknown error occurred!';
      console.error('HTTP Request Error:', error);
      
      if (error.status === 0) {
        errorMessage = 'Server is down.';
      } else if (error.status === 409) {
        errorMessage = `Conflict Error: ${error.error?.message || 'Resource conflict occurred.'}`;
      } else if (error.status === 422) {
        errorMessage = 'Validation Error:';
        if (error.error?.errors) {
          for (const err of error.error.errors) {
            errorMessage += `\n- ${err.msg}`;
          }
        } else {
          errorMessage = error.error?.message || 'Validation failed';
        }
      } else if (error.status >= 400 && error.status < 500) {
        errorMessage = `Client Error: ${error.error?.message || error.statusText}`;
      } else if (error.status >= 500) {
        errorMessage = 'Server error occurred. Please try again later.';
      }


        toastService.show('warn', errorMessage);


      // Pass the error along to the calling component if it needs local handling
      return throwError(() => error);
    })
  );
};
