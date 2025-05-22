export interface StudySession {
  id: number;
  timestamp: string;
  score_percentage: number;
  total_questions_in_session: number;
  correct_answers_in_session: number;
  status: 'in_progress' | 'completed' | 'abandoned';
  last_question_idx_viewed: number;
}

export interface UserResponse {
  id: number;
  test_session_id: number;
  question_id_original: string;
  user_answers_letters_json: string;
  is_correct: boolean;
  timestamp: string;
}