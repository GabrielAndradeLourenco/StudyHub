import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { QuestionService } from '../../services/question.service';
import { StudySessionService } from '../../services/study-session.service';
import { Question, Option } from '../../models/question.model';

@Component({
  selector: 'app-question',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './question.component.html',
  styleUrls: ['./question.component.scss']
})
export class QuestionComponent implements OnInit {
  question: Question | null = null;
  questionIndex: number = 0;
  totalQuestions: number = 0;
  selectedOptions: string[] = [];
  feedbackMessage: string = '';
  isCorrect: boolean | null = null;
  isAnswered: boolean = false;
  correctAnswer: string = '';
  examType: string = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private questionService: QuestionService,
    private studySessionService: StudySessionService
  ) { }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.examType = params['exam_type'] || '';
      const questionIdx = params['question_idx'];
      
      if (!this.examType) {
        console.error('exam_type é obrigatório');
        this.router.navigate(['/exam-selection']);
        return;
      }
      
      if (questionIdx !== undefined) {
        this.questionIndex = +questionIdx;
      } else {
        // Pegar do parâmetro da rota se existir
        this.route.params.subscribe(routeParams => {
          if (routeParams['id'] !== undefined) {
            this.questionIndex = +routeParams['id'];
          }
        });
      }
      
      this.loadTotalQuestions();
      this.loadQuestion();
    });
  }
  
  loadTotalQuestions(): void {
    this.questionService.getTotalQuestions(this.examType).subscribe({
      next: (count) => {
        this.totalQuestions = count;
      },
      error: (err) => console.error('Erro ao obter total de questões:', err)
    });
  }

  loadQuestion(): void {
    this.questionService.getQuestion(this.questionIndex, this.examType).subscribe({
      next: (question) => {
        this.question = question;
        this.selectedOptions = [];
        this.isAnswered = false;
        this.isCorrect = null;
        this.feedbackMessage = '';
      },
      error: (err) => {
        console.error('Erro ao carregar questão:', err);
        this.router.navigate(['/']);
      }
    });
  }

  toggleOption(letra: string): void {
    if (this.isAnswered) return;

    const index = this.selectedOptions.indexOf(letra);
    if (index === -1) {
      // Se a opção não estiver selecionada e ainda não atingimos o limite
      if (this.question && this.selectedOptions.length < this.question.num_answers_to_select) {
        this.selectedOptions.push(letra);
      } else if (this.question && this.selectedOptions.length >= this.question.num_answers_to_select) {
        // Se já atingimos o limite, substitua a primeira seleção
        this.selectedOptions.shift();
        this.selectedOptions.push(letra);
      }
    } else {
      // Se a opção já estiver selecionada, remova-a
      this.selectedOptions.splice(index, 1);
    }
  }

  isSelected(letra: string): boolean {
    return this.selectedOptions.includes(letra);
  }

  submitAnswer(): void {
    if (!this.question || this.isAnswered) return;

    if (this.question.num_answers_to_select !== this.selectedOptions.length) {
      this.feedbackMessage = `Você deve selecionar ${this.question.num_answers_to_select} opção(ões).`;
      return;
    }

    this.questionService.submitAnswer(this.question.id_original_json, this.selectedOptions, this.examType).subscribe({
      next: (response) => {
        this.isAnswered = true;
        this.isCorrect = response.is_correct;
        this.correctAnswer = response.correct_answer_was;
        this.feedbackMessage = response.is_correct ? 'Resposta correta!' : 'Resposta incorreta.';
      },
      error: (error) => {
        if (error.status === 409) {
          // Questão já respondida
          this.isAnswered = true;
          this.isCorrect = error.error.is_correct;
          this.correctAnswer = error.error.correct_answer_was;
          this.selectedOptions = error.error.previous_user_answers || [];
          this.feedbackMessage = 'Esta questão já foi respondida anteriormente.';
        } else {
          console.error('Erro ao enviar resposta:', error);
          this.feedbackMessage = 'Erro ao enviar resposta. Tente novamente.';
        }
      }
    });
  }

  nextQuestion(): void {
    this.router.navigate(['/question'], { 
      queryParams: { 
        exam_type: this.examType,
        question_idx: this.questionIndex + 1 
      } 
    });
  }

  previousQuestion(): void {
    if (this.questionIndex > 0) {
      this.router.navigate(['/question'], { 
        queryParams: { 
          exam_type: this.examType,
          question_idx: this.questionIndex - 1 
        } 
      });
    }
  }

  finishStudy(): void {
    this.studySessionService.finishStudy(this.examType).subscribe({
      next: (session) => {
        this.router.navigate(['/session-results', session.id]);
      },
      error: (err) => {
        console.error('Erro ao finalizar estudo:', err);
        this.router.navigate(['/']);
      }
    });
  }
}