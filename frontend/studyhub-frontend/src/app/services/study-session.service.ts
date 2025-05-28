import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StudySession } from '../models/study-session.model';

@Injectable({
  providedIn: 'root'
})
export class StudySessionService {
  private apiUrl = 'https://studyhub-backend-vr4x.onrender.com/api';

  constructor(private http: HttpClient) { }

  getCurrentSession(): Observable<StudySession | null> {
    return this.http.get<StudySession | null>(`${this.apiUrl}/current-session`);
  }

  startNewStudy(startQuestionIdx: number = 0): Observable<StudySession> {
    return this.http.post<StudySession>(`${this.apiUrl}/start-new-study`, { start_question_idx: startQuestionIdx });
  }

  resumeStudy(): Observable<StudySession> {
    return this.http.get<StudySession>(`${this.apiUrl}/resume-study`);
  }

  finishStudy(): Observable<StudySession> {
    return this.http.post<StudySession>(`${this.apiUrl}/finish-study`, {});
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