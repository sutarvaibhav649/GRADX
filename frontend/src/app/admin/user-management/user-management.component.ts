import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AdminService } from '../../shared/services/admin.service';
import { AuthService } from '../../shared/services/auth.service';
import { ToastService } from '../../shared/toast.service';

type UserRole = 'student' | 'faculty' | 'admin';

interface AdminUser {
  _id: string;
  fullName: string;
  email: string;
  role: UserRole;
  idNumber: string;
  department?: string;
  isActive: boolean;
  createdAt?: string;
}

@Component({
  selector: 'app-user-management',
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink],
  templateUrl: './user-management.component.html',
  styleUrl: './user-management.component.css',
})
export class UserManagementComponent implements OnInit {
  users: AdminUser[] = [];
  userForm!: FormGroup;
  isLoading = false;
  isSaving = false;
  editingUser: AdminUser | null = null;
  search = '';
  roleFilter = '';
  page = 1;
  limit = 10;
  totalPages = 1;
  totalUsers = 0;

  roles = [
    { value: 'student', label: 'Student' },
    { value: 'faculty', label: 'Faculty' },
    { value: 'admin', label: 'Administrator' },
  ];

  departments = [
    { value: 'cse', label: 'CSE' },
    { value: 'aiml', label: 'AIML' },
    { value: 'ds', label: 'DS' },
    { value: 'it', label: 'IT' },
    { value: 'ece', label: 'ECE' },
  ];

  get userInitial() {
    return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'A';
  }

  get userName() {
    return this.auth.getUser()?.fullName || 'Admin';
  }

  get showDepartment() {
    return this.userForm?.get('role')?.value !== 'admin';
  }

  constructor(
    private fb: FormBuilder,
    private adminService: AdminService,
    private auth: AuthService,
    private toastService: ToastService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeForm();
    this.loadUsers();
  }

  initializeForm(): void {
    this.userForm = this.fb.group({
      fullName: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      role: ['student', [Validators.required]],
      idNumber: ['', [Validators.required]],
      department: ['cse', [Validators.required]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      isActive: [true],
      sendProdUpdate: [false],
    });

    this.userForm.get('role')?.valueChanges.subscribe((role) => {
      const department = this.userForm.get('department');
      if (role === 'admin') {
        department?.clearValidators();
        department?.setValue('');
      } else {
        department?.setValidators(Validators.required);
        if (!department?.value) department?.setValue('cse');
      }
      department?.updateValueAndValidity();
    });
  }

  loadUsers(): void {
    this.isLoading = true;
    const params: any = { page: this.page, limit: this.limit };
    if (this.search.trim()) params.search = this.search.trim();
    if (this.roleFilter) params.role = this.roleFilter;

    this.adminService.getAllUsers(params).subscribe({
      next: (res) => {
        this.users = res.data || [];
        this.totalPages = res.pagination?.pages || 1;
        this.totalUsers = res.pagination?.total || this.users.length;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.toastService.show('error', err.error?.message || 'Failed to load users.');
      },
    });
  }

  applyFilters(): void {
    this.page = 1;
    this.loadUsers();
  }

  clearFilters(): void {
    this.search = '';
    this.roleFilter = '';
    this.applyFilters();
  }

  saveUser(): void {
    if (this.userForm.invalid) {
      this.userForm.markAllAsTouched();
      this.toastService.show('warn', 'Please complete the required user details.');
      return;
    }

    this.isSaving = true;
    const payload = this.buildPayload();
    const request = this.editingUser
      ? this.adminService.updateUser(this.editingUser._id, payload)
      : this.adminService.createUser(payload);

    request.subscribe({
      next: () => {
        this.isSaving = false;
        this.toastService.show('success', this.editingUser ? 'User updated successfully.' : 'User created successfully.');
        this.resetForm();
        this.loadUsers();
      },
      error: (err) => {
        this.isSaving = false;
        this.toastService.show('error', err.error?.message || 'Unable to save user.');
      },
    });
  }

  editUser(user: AdminUser): void {
    this.editingUser = user;
    this.userForm.patchValue({
      fullName: user.fullName,
      email: user.email,
      role: user.role,
      idNumber: user.idNumber,
      department: user.department || '',
      password: '',
      isActive: user.isActive,
      sendProdUpdate: false,
    });
    this.userForm.get('email')?.disable();
    this.userForm.get('role')?.disable();
    this.userForm.get('idNumber')?.disable();
    this.userForm.get('password')?.clearValidators();
    this.userForm.get('password')?.updateValueAndValidity();
  }

  resetForm(): void {
    this.editingUser = null;
    this.userForm.reset({
      fullName: '',
      email: '',
      role: 'student',
      idNumber: '',
      department: 'cse',
      password: '',
      isActive: true,
      sendProdUpdate: false,
    });
    this.userForm.get('email')?.enable();
    this.userForm.get('role')?.enable();
    this.userForm.get('idNumber')?.enable();
    this.userForm.get('password')?.setValidators([Validators.required, Validators.minLength(8)]);
    this.userForm.get('password')?.updateValueAndValidity();
  }

  toggleActive(user: AdminUser): void {
    this.adminService.updateUser(user._id, {
      fullName: user.fullName,
      department: user.department,
      isActive: !user.isActive,
    }).subscribe({
      next: () => {
        this.toastService.show('success', `User ${user.isActive ? 'deactivated' : 'activated'} successfully.`);
        this.loadUsers();
      },
      error: (err) => this.toastService.show('error', err.error?.message || 'Unable to update user status.'),
    });
  }

  deleteUser(user: AdminUser): void {
    const confirmed = confirm(`Delete ${user.fullName}? This action cannot be undone.`);
    if (!confirmed) return;

    this.adminService.deleteUser(user._id).subscribe({
      next: () => {
        this.toastService.show('success', 'User deleted successfully.');
        if (this.users.length === 1 && this.page > 1) this.page -= 1;
        this.loadUsers();
      },
      error: (err) => this.toastService.show('error', err.error?.message || 'Unable to delete user.'),
    });
  }

  goToPage(direction: number): void {
    const nextPage = this.page + direction;
    if (nextPage < 1 || nextPage > this.totalPages) return;
    this.page = nextPage;
    this.loadUsers();
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }

  private buildPayload(): any {
    const raw = this.userForm.getRawValue();
    const payload: any = {
      fullName: raw.fullName,
      department: raw.role === 'admin' ? undefined : raw.department,
      isActive: raw.isActive,
    };

    if (!this.editingUser) {
      payload.email = raw.email;
      payload.password = raw.password;
      payload.role = raw.role;
      payload.idNumber = raw.idNumber;
      payload.sendProdUpdate = raw.sendProdUpdate;
    }

    return payload;
  }
}
