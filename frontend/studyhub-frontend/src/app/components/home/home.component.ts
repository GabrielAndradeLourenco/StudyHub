import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { DatePipe } from '@angular/common';
import { QuestionService } from '../../services/question.service';
import { StudySessionService } from '../../services/study-session.service';
import { StudySession } from '../../models/study-session.model';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  numTotalQuestions = 0;
  inProgressSession: StudySession | null = null;

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

  startNewStudy(): void {
    this.studySessionService.startNewStudy().subscribe({
      next: () => this.router.navigate(['/question', 0]),
      error: err => console.error('Erro ao iniciar novo estudo:', err)
    });
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