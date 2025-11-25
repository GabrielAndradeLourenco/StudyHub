import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Exam } from '../models/exam.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ExamService {
  private apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  getAvailableExams(): Observable<Exam[]> {
    return this.http.get<Exam[]>(`${this.apiUrl}/exams`);
  }
}