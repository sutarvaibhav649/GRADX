import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app.component';

bootstrapApplication(App, appConfig)
  .catch((err:any) => {
    console.error('Application bootstrap failed:', err);
    document.body.innerHTML = '<div style="text-align: center; margin-top: 50px;"><h1>Application Error</h1><p>The application failed to load. Please refresh the page or contact support.</p></div>';
  });
