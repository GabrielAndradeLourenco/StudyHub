import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { StudySessionService } from '../../services/study-session.service';

@Component({
  selector: 'app-session-results',
  standalone: true,
  imports: [CommonModule, RouterModule, DatePipe],
  template: `
    <div class="container" *ngIf="sessionData">
      <div class="results-header">
        <h2>Resultados da Sessão</h2>
        <p class="lead">Sessão de {{ sessionData.session.timestamp | date:'dd/MM/yyyy HH:mm' }}</p>
      </div>
      
      <div class="session-summary">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Resumo</h5>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-label">Status</div>
                <div class="summary-value">
                  <span class="badge" [ngClass]="{
                    'bg-warning': sessionData.session.status === 'in_progress',
                    'bg-success': sessionData.session.status === 'completed',
                    'bg-secondary': sessionData.session.status === 'abandoned'
                  }">
                    {{ sessionData.session.status === 'in_progress' ? 'Em Progresso' : 
                       sessionData.session.status === 'completed' ? 'Completada' : 'Abandonada' }}
                  </span>
                </div>
              </div>
              
              <div class="summary-item">
                <div class="summary-label">Pontuação</div>
                <div class="summary-value">
                  <span class="score-badge" [ngClass]="{
                    'high-score': sessionData.session.score_percentage >= 70,
                    'medium-score': sessionData.session.score_percentage >= 40 && sessionData.session.score_percentage < 70,
                    'low-score': sessionData.session.score_percentage < 40
                  }">
                    {{ sessionData.session.score_percentage !== null ? (sessionData.session.score_percentage).toFixed(2) : '0.00' }}%
                  </span>
                </div>
              </div>
              
              <div class="summary-item">
                <div class="summary-label">Questões</div>
                <div class="summary-value">
                  {{ sessionData.session.correct_answers_in_session || 0 }}/{{ sessionData.session.total_questions_in_session || 0 }}
                  <small class="text-muted">({{ sessionData.session.total_questions_in_session ? ((sessionData.session.correct_answers_in_session / sessionData.session.total_questions_in_session) * 100).toFixed(0) : 0 }}% de acertos)</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="results-section">
        <h3>Respostas</h3>
        
        <div *ngIf="sessionData.results.length === 0" class="alert alert-info">
          <i class="bi bi-info-circle me-2"></i> Nenhuma resposta registrada nesta sessão.
        </div>
        
        <div *ngIf="sessionData.results.length > 0" class="results-table-container">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>Questão</th>
                <th>Resposta</th>
                <th>Resultado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let result of sessionData.results">
                <td>{{ result.question_title }}</td>
                <td>{{ result.user_answers }}</td>
                <td>
                  <span class="badge" [ngClass]="{
                    'bg-success': result.is_correct,
                    'bg-danger': !result.is_correct
                  }">
                    {{ result.is_correct ? 'Correta' : 'Incorreta' }}
                  </span>
                </td>
                <td>
                  <button *ngIf="result.question_idx !== null" 
                          [routerLink]="['/question', result.question_idx]" 
                          class="btn btn-sm btn-info">
                    <i class="bi bi-search"></i> Revisar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div class="mt-4 text-center">
        <button routerLink="/study-sessions" class="btn btn-secondary">
          <i class="bi bi-arrow-left"></i> Voltar para Histórico
        </button>
      </div>
    </div>
    
    <div class="container loading-container" *ngIf="!sessionData">
      <div class="loading-spinner">
        <i class="bi bi-arrow-repeat spin"></i>
        <p>Carregando resultados...</p>
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 1000px;
    }
    
    .results-header {
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
    
    .session-summary {
      margin-bottom: 30px;
      
      .card {
        border: none;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        
        .card-title {
          color: var(--secondary-color);
          font-weight: 600;
          border-bottom: 1px solid #eee;
          padding-bottom: 10px;
          margin-bottom: 15px;
        }
      }
      
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
      }
      
      .summary-item {
        .summary-label {
          font-size: 0.9rem;
          color: #666;
          margin-bottom: 5px;
        }
        
        .summary-value {
          font-size: 1.1rem;
          font-weight: 500;
        }
        
        .score-badge {
          font-weight: 600;
          padding: 5px 10px;
          border-radius: 4px;
          
          &.high-score {
            background-color: #d4edda;
            color: #155724;
          }
          
          &.medium-score {
            background-color: #fff3cd;
            color: #856404;
          }
          
          &.low-score {
            background-color: #f8d7da;
            color: #721c24;
          }
        }
      }
    }
    
    .results-section {
      h3 {
        color: var(--secondary-color);
        margin-bottom: 20px;
        font-weight: 600;
        font-size: 1.3rem;
      }
    }
    
    .results-table-container {
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
    
    .loading-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 300px;
      
      .loading-spinner {
        text-align: center;
        
        i {
          font-size: 3rem;
          color: var(--primary-color);
          animation: spin 1s linear infinite;
        }
        
        p {
          margin-top: 15px;
          color: #666;
        }
      }
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class SessionResultsComponent implements OnInit {
  sessionData: any = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private studySessionService: StudySessionService
  ) { }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      const sessionId = +params['id'];
      this.loadSessionResults(sessionId);
    });
  }

  loadSessionResults(sessionId: number): void {
    this.studySessionService.getSessionResults(sessionId).subscribe({
      next: data => this.sessionData = data,
      error: err => {
        console.error('Erro ao carregar resultados da sessão:', err);
        this.router.navigate(['/study-sessions']);
      }
    });
  }
}