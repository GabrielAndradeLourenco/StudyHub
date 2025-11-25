import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StudySession } from '../models/study-session.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class StudySessionService {
  private apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  getCurrentSession(examType: string): Observable<StudySession | null> {
    return this.http.get<StudySession | null>(`${this.apiUrl}/current-session?exam_type=${examType}`);
  }

  startNewStudy(startQuestionIdx: number, examType: string): Observable<StudySession> {
    return this.http.post<StudySession>(`${this.apiUrl}/start-new-study`, {
      start_question_idx: startQuestionIdx,
      exam_type: examType
    });
  }

  resumeStudy(examType: string): Observable<StudySession> {
    return this.http.get<StudySession>(`${this.apiUrl}/resume-study?exam_type=${examType}`);
  }

  finishStudy(examType: string): Observable<StudySession> {
    return this.http.post<StudySession>(`${this.apiUrl}/finish-study`, {
      exam_type: examType
    });
  }

  getAllSessions(): Observable<StudySession[]> {
    return this.http.get<StudySession[]>(`${this.apiUrl}/study-sessions`);
  }

  getSessionResults(sessionId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/results/session/${sessionId}`);
  }

  deleteSession(sessionId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/session/${sessionId}`);
  }
}