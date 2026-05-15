import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export type ToastType = 'info' | 'success' | 'warn' | 'error';

export interface Toast {
  type: ToastType;
  message: string;
  id: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastSubject = new Subject<Toast>();
  toasts$ = this.toastSubject.asObservable();
  private counter = 0;

  show(type: ToastType, message: string): void {
    const id = this.counter++;
    console.log('Toast Service - Showing toast:', { type, message, id });
    this.toastSubject.next({ type, message, id });
  }
}
