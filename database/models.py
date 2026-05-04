from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum, JSON, Float, LargeBinary
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    full_name = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    language_code = Column(String(10), default="uz")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lessons_created = relationship("Lesson", back_populates="creator")
    submissions = relationship("Submission", back_populates="student")
    grades = relationship("Grade", back_populates="grader")
    notifications = relationship("Notification", back_populates="user")

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User")
    lessons = relationship("Lesson", back_populates="subject")
    categories = relationship("Category", back_populates="subject")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subject = relationship("Subject", back_populates="categories")
    parent = relationship("Category", remote_side=[id])
    lessons = relationship("Lesson", back_populates="category")

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    objectives = Column(Text)
    keywords = Column(JSON)  # List of keywords
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled publishing
    is_published = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)  # Student completion
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subject = relationship("Subject", back_populates="lessons")
    category = relationship("Category", back_populates="lessons")
    creator = relationship("User", back_populates="lessons_created")
    files = relationship("File", back_populates="lesson")
    quizzes = relationship("Quiz", back_populates="lesson")
    homework = relationship("Homework", back_populates="lesson")

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    file_id = Column(String(500), nullable=False)  # Telegram file_id
    file_type = Column(String(20), nullable=False)  # pdf, docx, pptx, jpg, etc.
    file_name = Column(String(300), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    lesson = relationship("Lesson", back_populates="files")
    uploader = relationship("User")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    time_limit = Column(Integer)  # in seconds
    max_attempts = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    lesson = relationship("Lesson", back_populates="quizzes")
    creator = relationship("User")
    questions = relationship("QuizQuestion", back_populates="quiz", order_by="QuizQuestion.order")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="multiple_choice")  # multiple_choice, true_false, short_answer
    points = Column(Integer, default=1)
    order = Column(Integer, nullable=False)
    explanation = Column(Text)  # Explanation for the answer
    
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question")

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("QuizQuestion", back_populates="answers")

class Homework(Base):
    __tablename__ = "homework"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False)
    max_score = Column(Integer, default=100)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lesson = relationship("Lesson", back_populates="homework")
    creator = relationship("User")
    submissions = relationship("Submission", back_populates="homework")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    homework_id = Column(Integer, ForeignKey("homework.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text)  # Text submission
    file_id = Column(String(500))  # If file submitted
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_graded = Column(Boolean, default=False)
    
    homework = relationship("Homework", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    grade = relationship("Grade", back_populates="submission", uselist=False)

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    graded_at = Column(DateTime, default=datetime.utcnow)
    
    submission = relationship("Submission", back_populates="grade")
    grader = relationship("User", back_populates="grades")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # deadline, announcement, reminder
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="notifications")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "lesson_created", "file_uploaded"
    details = Column(JSON)  # Additional details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    lesson = relationship("Lesson")

class Progress(Base):
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    quiz_score = Column(Float, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    lesson = relationship("Lesson")