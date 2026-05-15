import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../shared/services/auth.service';
import { ToastService } from '../../shared/toast.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  loginData: FormGroup;
  isLoading = false;

  constructor(private fb: FormBuilder, private auth: AuthService, private toastService: ToastService, private router: Router) {
    this.loginData = fb.group({
      role: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]],
      rememberMe: [false]
    });
  }

  submit() {
    if (this.loginData.invalid) {
      this.loginData.markAllAsTouched();
      this.toastService.show('error', 'Please fill out all required fields correctly.');
      return;
    }

    this.isLoading = true;
    const { email, password, role } = this.loginData.value;

    this.auth.login(email, password, role).subscribe({
      next: (res) => {
        this.isLoading = false;
        const userRole = res.user.role;
        this.toastService.show('success', 'Login successful. Redirecting to dashboard...');
        this.router.navigate([`/${userRole}/dashboard`]);
      },
      error: (err) => {
        this.isLoading = false;
      }
    });
  }
}
