import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QuestionService } from '../../services/question.service';
import { StudySessionService } from '../../services/study-session.service';
import { StudySession } from '../../models/study-session.model';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, DatePipe, FormsModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  numTotalQuestions = 0;
  inProgressSession: StudySession | null = null;
  selectedQuestionNumber = 1;

  constructor(
    private questionService: QuestionService,
    private studySessionService: StudySessionService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadTotalQuestions();
    this.checkForInProgressSession();
  }

  loadTotalQuestions(): void {
    this.questionService.getTotalQuestions().subscribe({
      next: count => this.numTotalQuestions = count,
      error: err => console.error('Erro ao carregar total de questões:', err)
    });
  }

  checkForInProgressSession(): void {
    this.studySessionService.getCurrentSession().subscribe({
      next: session => this.inProgressSession = session,
      error: err => console.error('Erro ao verificar sessão em progresso:', err)
    });
  }

  startNewStudy(startQuestionIdx: number = 0): void {
    this.studySessionService.startNewStudy(startQuestionIdx).subscribe({
      next: (session) => this.router.navigate(['/question', session.last_question_idx_viewed]),
      error: err => console.error('Erro ao iniciar novo estudo:', err)
    });
  }
  
  openQuestionSelector(): void {
    const questionSelector = document.getElementById('questionSelectorModal');
    if (questionSelector) {
      (questionSelector as any).style.display = 'block';
    }
  }
  
  closeQuestionSelector(): void {
    const questionSelector = document.getElementById('questionSelectorModal');
    if (questionSelector) {
      (questionSelector as any).style.display = 'none';
    }
  }
  
  startFromSelectedQuestion(questionNumber: number): void {
    // Ajusta para índice baseado em zero
    const questionIdx = Math.max(0, questionNumber - 1);
    
    // Verifica se o índice é válido
    if (questionIdx >= 0 && questionIdx < this.numTotalQuestions) {
      this.startNewStudy(questionIdx);
      this.closeQuestionSelector();
    }
  }

  resumeStudy(): void {
    if (this.inProgressSession) {
      const questionIdx = this.inProgressSession.last_question_idx_viewed || 0;
      this.router.navigate(['/question', questionIdx]);
    }
  }

  viewStudySessions(): void {
    this.router.navigate(['/study-sessions']);
  }

  runScraper(): void {
    // Implementar chamada para executar o scraper
  }
}