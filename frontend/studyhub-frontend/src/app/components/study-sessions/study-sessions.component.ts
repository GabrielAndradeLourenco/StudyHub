import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { StudySessionService } from '../../services/study-session.service';
import { StudySession } from '../../models/study-session.model';

@Component({
  selector: 'app-study-sessions',
  standalone: true,
  imports: [CommonModule, RouterModule, DatePipe],
  template: `
    <div class="container">
      <div class="sessions-header">
        <h2>Meu Histórico de Estudos</h2>
        <p class="lead">Visualize e gerencie suas sessões de estudo anteriores</p>
      </div>
      
      <div *ngIf="sessions.length === 0" class="alert alert-info">
        <i class="bi bi-info-circle me-2"></i> Nenhuma sessão de estudo encontrada.
      </div>
      
      <div *ngIf="sessions.length > 0" class="sessions-table-container">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>Data</th>
              <th>Status</th>
              <th>Pontuação</th>
              <th>Questões</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let session of sessions">
              <td>{{ session.timestamp | date:'dd/MM/yyyy HH:mm' }}</td>
              <td>
                <span class="badge" [ngClass]="{
                  'bg-warning': session.status === 'in_progress',
                  'bg-success': session.status === 'completed',
                  'bg-secondary': session.status === 'abandoned'
                }">
                  {{ session.status === 'in_progress' ? 'Em Progresso' : 
                     session.status === 'completed' ? 'Completada' : 'Abandonada' }}
                </span>
              </td>
              <td>{{ session.score_percentage !== null ? (session.score_percentage).toFixed(2) : '0.00' }}%</td>
              <td>{{ session.correct_answers_in_session || 0 }}/{{ session.total_questions_in_session || 0 }}</td>
              <td class="actions-column">
                <button [routerLink]="['/session-results', session.id]" class="btn btn-sm btn-info me-2">
                  <i class="bi bi-eye"></i> Detalhes
                </button>
                <button (click)="deleteSession(session.id)" class="btn btn-sm btn-danger">
                  <i class="bi bi-trash"></i> Excluir
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="mt-4 text-center">
        <button routerLink="/" class="btn btn-secondary">
          <i class="bi bi-arrow-left"></i> Voltar para Início
        </button>
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 1000px;
    }
    
    .sessions-header {
      text-align: center;
      margin-bottom: 30px;
      
      h2 {
        color: var(--secondary-color);
        margin-bottom: 10px;
        font-weight: 600;
      }
      
      .lead {
        color: #666;
      }
    }
    
    .sessions-table-container {
      margin: 20px 0;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
      border-radius: 8px;
      overflow: hidden;
      
      table {
        margin-bottom: 0;
        
        th {
          background-color: #f8f9fa;
          font-weight: 600;
          color: var(--secondary-color);
        }
        
        td, th {
          padding: 12px 15px;
          vertical-align: middle;
        }
      }
    }
    
    .actions-column {
      white-space: nowrap;
    }
    
    .badge {
      padding: 6px 10px;
      font-weight: 500;
    }
  `]
})
export class StudySessionsComponent implements OnInit {
  sessions: StudySession[] = [];

  constructor(private studySessionService: StudySessionService) { }

  ngOnInit(): void {
    this.loadSessions();
  }

  loadSessions(): void {
    this.studySessionService.getAllSessions().subscribe({
      next: sessions => this.sessions = sessions,
      error: err => console.error('Erro ao carregar sessões:', err)
    });
  }

  deleteSession(sessionId: number): void {
    if (confirm('Tem certeza que deseja excluir esta sessão?')) {
      this.studySessionService.deleteSession(sessionId).subscribe({
        next: () => {
          this.sessions = this.sessions.filter(s => s.id !== sessionId);
        },
        error: err => console.error('Erro ao excluir sessão:', err)
      });
    }
  }
}