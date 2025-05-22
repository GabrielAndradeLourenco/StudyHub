import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'question/:id', loadComponent: () => import('./components/question/question.component').then(m => m.QuestionComponent) },
  { path: 'study-sessions', loadComponent: () => import('./components/study-sessions/study-sessions.component').then(m => m.StudySessionsComponent) },
  { path: 'session-results/:id', loadComponent: () => import('./components/session-results/session-results.component').then(m => m.SessionResultsComponent) },
  { path: '**', redirectTo: '' }
];