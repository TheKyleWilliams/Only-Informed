from datetime import datetime, timezone
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.sql import expression
import json

@login_manager.user_loader  # Flask-Login Decorator
def load_user(user_id):
    # Fetches user object from User table
    return User.query.get(int(user_id))

# User Entity - db.Model maps to database table, UserMixin is Flask-Login mixin
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    # define attributes, id = primary key 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    # relationships 
    comments = db.relationship('Comment', backref='author', lazy=True)
    quizzes = db.relationship('UserQuiz', back_populates='user')  # Updated relationship

    # defines string representation for User object 
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Article Entity 
class Article(db.Model):
    __tablename__ = 'article'

    # define attributes 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    image_url = db.Column(db.String(500), nullable=True)  # New field for main image

    # relationships 
    quiz = db.relationship('Quiz', uselist=False, backref='article')  # uselist=False indicates a 1-to-1 relationship with quiz
    comments = db.relationship('Comment', backref='article', lazy=True)

    # string representation for Article object
    def __repr__(self):
        return f"Article('{self.title}', '{self.source}')"

# Quiz Entity
class Quiz(db.Model):
    __tablename__ = 'quiz'

    # attributes
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', name="fk_quiz_article"), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # store as JSON string
    date_generated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    users = db.relationship('UserQuiz', back_populates='quiz')  # Updated relationship

    # string representation of Quiz object 
    def __repr__(self):
        return f"Quiz(Article ID: {self.article_id}, Generated: {self.date_generated})"

# Comment Entity
class Comment(db.Model):
    __tablename__ = 'comment'

    # attributes
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name="fk_comment_user"), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', name="fk_comment_article"), nullable=False)

    # string representation of Comment object
    def __repr__(self):
        return f"Comment('{self.content[:20]}')"

# Association Model for User <-> Quiz
# This replaces the db.Table for user_quiz
class UserQuiz(db.Model):
    __tablename__ = 'user_quiz'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name="fk_user_quiz_user"), primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', name="fk_user_quiz_quiz"), primary_key=True)
    passed = db.Column(db.Boolean, nullable=False, default=False)
    attempted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, nullable=True)
    results_json = db.Column(db.Text, nullable=True) 

    # Relationships
    user = db.relationship('User', back_populates='quizzes')
    quiz = db.relationship('Quiz', back_populates='users')

    # string representation of UserQuiz object
    def __repr__(self):
        return f"UserQuiz(User ID: {self.user_id}, Quiz ID: {self.quiz_id}, Passed: {self.passed})"