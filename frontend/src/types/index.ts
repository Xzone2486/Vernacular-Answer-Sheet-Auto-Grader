export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Evaluator {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Student {
  id: number;
  name: string;
  roll_no: string;
}

export interface Exam {
  id: number;
  name: string;
  created_at: string;
}

export interface QuestionBrief {
  id: number;
  text: string;
  max_marks: number;
}

export interface ExamDetail extends Exam {
  questions: QuestionBrief[];
}

export interface Question {
  id: number;
  exam_id: number;
  text: string;
  max_marks: number;
}

export interface ReferenceAnswer {
  id: number;
  question_id: number;
  text: string;
  rubric_keywords: string[] | null;
}

export interface StudentAnswer {
  id: number;
  answer_sheet_id: number;
  question_id: number | null;
  ocr_text: string | null;
  ocr_confidence: number | null;
}

export interface AnswerSheet {
  id: number;
  student_id: number;
  exam_id: number;
  image_path: string;
  upload_time: string;
  student_answers: StudentAnswer[];
}

export interface Score {
  id: number;
  student_answer_id: number;
  auto_score: number | null;
  final_score: number | null;
  similarity_score: number | null;
  explanation: string | null;
}

export interface ScoringResult {
  similarity_score: number;
  awarded_marks: number;
  max_marks: number;
  matched_keywords: string[];
  missing_keywords: string[];
  explanation: string;
  needs_review: boolean;
}

export interface BatchUploadResult {
  filename: string;
  answer_sheet_id: number | null;
  error: string | null;
}

export interface BatchUploadResponse {
  uploaded: number;
  failed: number;
  results: BatchUploadResult[];
}

export interface BatchJobResponse {
  job_id: string;
  description: string;
  total: number;
  status: string;
}

export interface JobStatusResponse {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  description: string;
  created_at: string;
  updated_at: string;
  processed: number;
  total: number;
  error: string | null;
}
