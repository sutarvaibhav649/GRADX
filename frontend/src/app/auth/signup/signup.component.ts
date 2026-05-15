import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../shared/services/auth.service';
import { ToastService } from '../../shared/toast.service';

@Component({
  selector: 'app-signup',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.css',
})
export class SignupComponent implements OnInit {
  signUpData!: FormGroup;
  isLoading = false;
  showDepartment = true;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private toastService: ToastService,
    private router: Router
  ) {

  }
  ngOnInit(): void {
    this.initializeForm();
  }

  initializeForm() {
    this.signUpData = this.fb.group({
      role: ['', [Validators.required]],
      fullName: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      idNumber: ['', [Validators.required]],
      department: ['', [Validators.required]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]],
      agreeTandC: [false],
      sendProdUpdate: [false]
    }, { validators: this.passwordMatchValidator });
  }

  private passwordMatchValidator(g: FormGroup) {
    const password = g.get('password')?.value;
    const confirm = g.get('confirmPassword')?.value;

    if (!password || !confirm) return null;

    if (password !== confirm) {
      g.get('confirmPassword')?.setErrors({ mismatch: true });
      return { mismatch: true };
    } else {
      const errors = g.get('confirmPassword')?.errors;
      if (errors) {
        delete errors['mismatch'];
        g.get('confirmPassword')?.setErrors(Object.keys(errors).length ? errors : null);
      }
      return null;
    }
  }

  toggleSignupFields() {
    const role = this.signUpData.get('role')?.value;
    this.showDepartment = role !== 'admin';
    if (!this.showDepartment) {
      this.signUpData.get('department')?.clearValidators();
      this.signUpData.get('department')?.setValue('');
    } else {
      this.signUpData.get('department')?.setValidators(Validators.required);
    }
    this.signUpData.get('department')?.updateValueAndValidity();
  }

  signup() {
    if (this.signUpData.invalid) {
      this.signUpData.markAllAsTouched();
      this.toastService.show('warn', 'Please fill out all required fields correctly.');
      return;
    }
    if (!this.signUpData.get('agreeTandC')?.value) {
      this.toastService.show('warn', 'Please agree to the Terms & Conditions.');
      return;
    }
    this.isLoading = true;
    const { agreeTandC, ...payload } = this.signUpData.value;
    this.auth.signup(payload).subscribe({
      next: (val) => {
        const userRole = val.user.role;
        this.isLoading = false;
        this.toastService.show('success', val.message || 'Account created successfully!');
        this.router.navigate([`/${userRole}/dashboard`]);
      },
      error: (err: any) => {
        console.log('Signup error:', err);
        this.isLoading = false;
      }
    });
  }
}
