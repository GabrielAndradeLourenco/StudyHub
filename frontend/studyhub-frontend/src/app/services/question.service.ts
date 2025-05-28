import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Question } from '../models/question.model';

@Injectable({
  providedIn: 'root'
})
export class QuestionService {
  private apiUrl = 'https://studyhub-backend-vr4x.onrender.com/api';

  constructor(private http: HttpClient) { }

  getTotalQuestions(): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/questions/count`);
  }

  getQuestion(questionIdx: number): Observable<Question> {
    return this.http.get<Question>(`${this.apiUrl}/questions/${questionIdx}`);
  }

  submitAnswer(questionId: string, chosenLetters: string[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/submit_answer`, {
      question_id_original: questionId,
      chosen_letters: chosenLetters
    });
  }
}