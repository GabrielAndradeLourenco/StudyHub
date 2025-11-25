import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Question } from '../models/question.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class QuestionService {
  private apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  getTotalQuestions(examType: string): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/questions/count?exam_type=${examType}`);
  }

  getQuestion(questionIdx: number, examType: string): Observable<Question> {
    return this.http.get<Question>(`${this.apiUrl}/questions/${questionIdx}?exam_type=${examType}`);
  }

  submitAnswer(questionId: string, chosenLetters: string[], examType: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/submit_answer`, {
      question_id_original: questionId,
      chosen_letters: chosenLetters,
      exam_type: examType
    });
  }
}