import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { environment } from './environments/environment';

// Forçar o uso do ambiente de produção quando não estiver em desenvolvimento
if (environment.production) {
  console.log('Executando em ambiente de produção');
  // Garantir que o ambiente de produção seja usado
}

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
