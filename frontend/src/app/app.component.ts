import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastComponent } from './shared/toast/toast.component';
import { ToastService } from './shared/toast.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, ToastComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class App {
  constructor(
    private toastService: ToastService
  ) {}
  show() {
    this.toastService.show('success', 'This is a success message!');
  }
}
