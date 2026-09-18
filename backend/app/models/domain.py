from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, unique=True, index=True, nullable=False)

    answer_sheets = relationship("AnswerSheet", back_populates="student")

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="exam")
    answer_sheets = relationship("AnswerSheet", back_populates="exam")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    text = Column(Text, nullable=False)
    max_marks = Column(Float, nullable=False)

    exam = relationship("Exam", back_populates="questions")
    reference_answer = relationship("ReferenceAnswer", back_populates="question", uselist=False)

class ReferenceAnswer(Base):
    __tablename__ = "reference_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    rubric_keywords = Column(JSONB)

    question = relationship("Question", back_populates="reference_answer")

class AnswerSheet(Base):
    __tablename__ = "answer_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    image_path = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="answer_sheets")
    exam = relationship("Exam", back_populates="answer_sheets")
    student_answers = relationship("StudentAnswer", back_populates="answer_sheet")

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_sheet_id = Column(Integer, ForeignKey("answer_sheets.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)

    answer_sheet = relationship("AnswerSheet", back_populates="student_answers")
    question = relationship("Question")
    score = relationship("Score", back_populates="student_answer", uselist=False)

class Score(Base):
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    student_answer_id = Column(Integer, ForeignKey("student_answers.id"), unique=True, nullable=False)
    auto_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    evaluator_id = Column(Integer, nullable=True)
    override_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    student_answer = relationship("StudentAnswer", back_populates="score")
