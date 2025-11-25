import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ExamService } from '../../services/exam.service';
import { StudySessionService } from '../../services/study-session.service';
import { Exam } from '../../models/exam.model';

@Component({
  selector: 'app-exam-selection',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mt-4">
      <div class="row justify-content-center">
        <div class="col-md-10">
          <h2 class="text-center mb-4">Escolha seu Simulado AWS</h2>
          
          <div *ngIf="loading" class="text-center">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Carregando...</span>
            </div>
          </div>
          
          <div *ngIf="!loading" class="row">
            <div class="col-lg-4 col-md-6 mb-4" *ngFor="let exam of exams">
              <div class="card h-100 exam-card">
                <div class="card-body d-flex flex-column">
                  <h6 class="card-title">{{ exam.name }}</h6>
                  <p class="card-text text-muted small">
                    <i class="bi bi-question-circle"></i> {{ exam.question_count }} questões válidas
                  </p>
                  
                  <!-- Opção de questão inicial -->
                  <div class="mb-3" *ngIf="selectedExamForStart === exam.id">
                    <label class="form-label small">Questão inicial (opcional):</label>
                    <input 
                      type="number" 
                      class="form-control form-control-sm" 
                      [(ngModel)]="startQuestionNumber"
                      [min]="1" 
                      [max]="exam.question_count"
                      placeholder="1">
                  </div>
                  
                  <div class="mt-auto">
                    <div class="d-grid gap-2">
                      <button 
                        class="btn btn-primary btn-sm" 
                        (click)="toggleStartOptions(exam.id)"
                        *ngIf="selectedExamForStart !== exam.id">
                        <i class="bi bi-play-circle"></i> Novo Simulado
                      </button>
                      
                      <button 
                        class="btn btn-success btn-sm" 
                        (click)="startNewExam(exam.id)"
                        *ngIf="selectedExamForStart === exam.id">
                        <i class="bi bi-play-fill"></i> Iniciar
                      </button>
                      
                      <button 
                        class="btn btn-outline-secondary btn-sm" 
                        (click)="continueExam(exam.id)">
                        <i class="bi bi-arrow-clockwise"></i> Continuar
                      </button>
                      
                      <button 
                        class="btn btn-outline-danger btn-sm" 
                        (click)="cancelStart()"
                        *ngIf="selectedExamForStart === exam.id">
                        <i class="bi bi-x"></i> Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="text-center mt-4">
            <button class="btn btn-outline-secondary" (click)="goBack()">
              <i class="bi bi-arrow-left"></i> Voltar ao Menu
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .exam-card {
      transition: all 0.3s ease;
      border: 1px solid #e3e6f0;
      border-radius: 12px;
      overflow: hidden;
      height: 100%;
    }
    .exam-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 25px rgba(0,0,0,0.15);
      border-color: #667eea;
    }
    .card-title {
      font-size: 0.85rem;
      line-height: 1.3;
      min-height: 2.6rem;
      font-weight: 600;
      color: #2c3e50;
    }
    .card-text {
      color: #6c757d;
      font-size: 0.8rem;
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.3s ease;
    }
    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .btn-outline-secondary {
      border-radius: 8px;
      font-weight: 500;
    }
    .loading-spinner {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;
    }
    .spinner-border {
      color: #667eea;
    }
  `]
})
export class ExamSelectionComponent implements OnInit {
  exams: Exam[] = [];
  loading: boolean = true;
  selectedExamForStart: string | null = null;
  startQuestionNumber: number | null = null;

  constructor(
    private examService: ExamService,
    private studySessionService: StudySessionService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadExams();
  }

  loadExams(): void {
    this.examService.getAvailableExams().subscribe({
      next: (exams) => {
        this.exams = exams.sort((a, b) => a.name.localeCompare(b.name));
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar simulados:', err);
        this.loading = false;
      }
    });
  }

  toggleStartOptions(examId: string): void {
    this.selectedExamForStart = examId;
    this.startQuestionNumber = null;
  }

  cancelStart(): void {
    this.selectedExamForStart = null;
    this.startQuestionNumber = null;
  }

  startNewExam(examType: string): void {
    const startIdx = this.startQuestionNumber ? this.startQuestionNumber - 1 : 0;
    
    this.studySessionService.startNewStudy(startIdx, examType).subscribe({
      next: () => {
        this.router.navigate(['/question'], { 
          queryParams: { 
            exam_type: examType,
            question_idx: startIdx 
          }
        });
      },
      error: (err) => console.error('Erro ao iniciar simulado:', err)
    });
  }

  continueExam(examType: string): void {
    this.studySessionService.resumeStudy(examType).subscribe({
      next: (session) => {
        const questionIdx = session.last_question_idx_viewed || 0;
        this.router.navigate(['/question'], { 
          queryParams: { 
            exam_type: examType,
            question_idx: questionIdx 
          }
        });
      },
      error: (err) => console.error('Erro ao continuar simulado:', err)
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }
}