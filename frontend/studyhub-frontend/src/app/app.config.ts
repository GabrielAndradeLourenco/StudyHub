import { ApplicationConfig, importProvidersFrom, provideZoneChangeDetection, isDevMode } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(),
    importProvidersFrom(NgbModule),
    { provide: 'IS_PRODUCTION', useValue: !isDevMode() }
  ]
};