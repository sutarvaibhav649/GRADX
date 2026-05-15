import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { Toast, ToastService } from '../toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.component.html',
  styleUrls: ['./toast.component.css']
})
export class ToastComponent implements OnInit, OnDestroy {
  toasts: Toast[] = [];
  private subscription!: Subscription;

  constructor(
    private toastService: ToastService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
    console.log('ToastComponent - Constructor called');
  }

  ngOnInit(): void {
    console.log('ToastComponent - ngOnInit called');
    this.subscription = this.toastService.toasts$.subscribe(toast => {
      console.log('ToastComponent - Received toast:', toast);
      this.toasts.push(toast);
      this.changeDetectorRef.markForCheck();
      setTimeout(() => this.remove(toast.id), 3000);
    });
  }

  remove(id: number): void {
    console.log('ToastComponent - Removing toast:', id);
    this.toasts = this.toasts.filter(t => t.id !== id);
    this.changeDetectorRef.markForCheck();
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
