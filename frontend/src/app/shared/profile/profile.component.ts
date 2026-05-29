import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { ToastService } from '../toast.service';

type UserRole = 'student' | 'faculty' | 'admin';

@Component({
  selector: 'app-profile',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css',
})
export class ProfileComponent implements OnInit {
  profileForm!: FormGroup;
  passwordForm!: FormGroup;
  isSavingProfile = false;
  isSavingPassword = false;

  readonly departments = [
    { value: 'cse', label: 'Computer Science' },
    { value: 'aiml', label: 'AI & ML' },
    { value: 'ds', label: 'Data Science' },
    { value: 'it', label: 'IT' },
    { value: 'ece', label: 'Electronics' },
  ];

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.initForms();
    this.loadProfile();
  }

  get user() {
    return this.auth.getUser();
  }

  get role(): UserRole {
    return this.user?.role || 'student';
  }

  get roleLabel(): string {
    const labels: Record<UserRole, string> = {
      student: 'Student',
      faculty: 'Faculty',
      admin: 'Administrator',
    };
    return labels[this.role];
  }

  get dashboardLink(): string {
    return `/${this.role}/dashboard`;
  }

  get showDepartment(): boolean {
    return this.role !== 'admin';
  }

  get userInitial(): string {
    return this.user?.fullName?.charAt(0)?.toUpperCase() || this.roleLabel.charAt(0);
  }

  private initForms() {
    this.profileForm = this.fb.group({
      fullName: ['', Validators.required],
      email: [{ value: '', disabled: true }],
      role: [{ value: '', disabled: true }],
      idNumber: ['', Validators.required],
      department: [''],
      sendProdUpdate: [false],
    });

    this.passwordForm = this.fb.group(
      {
        currentPassword: ['', Validators.required],
        newPassword: ['', [Validators.required, Validators.minLength(8)]],
        confirmPassword: ['', Validators.required],
      },
      { validators: this.passwordMatchValidator }
    );
  }

  private loadProfile() {
    const user = this.auth.getUser();
    if (!user) {
      this.router.navigate(['/auth/login']);
      return;
    }

    if (this.showDepartment) {
      this.profileForm.get('department')?.setValidators(Validators.required);
    } else {
      this.profileForm.get('department')?.clearValidators();
    }
    this.profileForm.get('department')?.updateValueAndValidity();

    this.profileForm.patchValue({
      fullName: user.fullName || '',
      email: user.email || '',
      role: this.roleLabel,
      idNumber: user.idNumber || '',
      department: user.department || '',
      sendProdUpdate: user.sendProdUpdate === true,
    });
  }

  private passwordMatchValidator(group: FormGroup) {
    const next = group.get('newPassword')?.value;
    const confirm = group.get('confirmPassword')?.value;
    return next && confirm && next !== confirm ? { passwordMismatch: true } : null;
  }

  saveProfile() {
    if (this.profileForm.invalid) {
      this.profileForm.markAllAsTouched();
      this.toastService.show('warn', 'Please fill out the required profile fields.');
      return;
    }

    const raw = this.profileForm.getRawValue();
    const payload: any = {
      fullName: raw.fullName,
      idNumber: raw.idNumber,
      sendProdUpdate: raw.sendProdUpdate,
    };

    if (this.showDepartment) {
      payload.department = raw.department;
    }

    this.isSavingProfile = true;
    this.auth.updateProfile(payload).subscribe({
      next: (res) => {
        this.isSavingProfile = false;
        this.toastService.show('success', res.message || 'Profile updated successfully.');
        this.loadProfile();
      },
      error: (err) => {
        this.isSavingProfile = false;
        this.toastService.show('error', err.error?.message || 'Could not update profile.');
      },
    });
  }

  savePassword() {
    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      this.toastService.show('warn', 'Please check the password fields.');
      return;
    }

    const { currentPassword, newPassword } = this.passwordForm.value;
    this.isSavingPassword = true;
    this.auth.changePassword(currentPassword, newPassword).subscribe({
      next: (res) => {
        this.isSavingPassword = false;
        this.passwordForm.reset();
        this.toastService.show('success', res.message || 'Password updated successfully.');
      },
      error: (err) => {
        this.isSavingPassword = false;
        this.toastService.show('error', err.error?.message || 'Could not update password.');
      },
    });
  }
}
