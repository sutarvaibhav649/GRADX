import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { PageNotExistComponent } from './page-not-exist/page-not-exist.component';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full'
    },
    {
        path: 'home',
        component: HomeComponent
    },
    {
        path: 'admin',
        loadChildren: () =>
            import('./admin/admin.routes').then( m => m.adminRoutes )
    },
    {
        path: 'student',
        loadChildren: () =>
            import('./student/student.routes').then( m => m.studentRoutes )
    },
    {
        path: 'faculty',
        loadChildren: () =>
            import('./faculty/faculty.routes').then( m => m.facultyRoutes )
    },
    {
        path: 'auth',
        loadChildren: () =>
            import('./auth/auth.routes').then( m => m.authRoutes )
    },
    {
        path: 'model',
        loadChildren: () =>
            import('./AI-model/ai-model.routes').then( m => m.aiModelRoutes )
    },
    {
        path: '**',
        component: PageNotExistComponent
    }
];
