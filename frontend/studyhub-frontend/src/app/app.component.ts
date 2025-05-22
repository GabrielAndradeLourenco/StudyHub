import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StudySessionService } from './services/study-session.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'StudyHub';
  currentYear = new Date().getFullYear();
  
  constructor(
    private router: Router,
    private studySessionService: StudySessionService
  ) {}
  
  startNewStudy(): void {
    this.studySessionService.startNewStudy().subscribe({
      next: () => this.router.navigate(['/question', 0]),
      error: (err) => console.error('Erro ao iniciar novo estudo:', err)
    });
  }
}