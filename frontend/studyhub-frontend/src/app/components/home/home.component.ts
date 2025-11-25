import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StudySessionService } from '../../services/study-session.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  constructor(
    private studySessionService: StudySessionService,
    private router: Router
  ) { }

  ngOnInit(): void {
    // Não carrega sessão automaticamente - usuário deve escolher o exame
  }

  selectExam(): void {
    this.router.navigate(['/exam-selection']);
  }

  viewStudySessions(): void {
    this.router.navigate(['/study-sessions']);
  }


}