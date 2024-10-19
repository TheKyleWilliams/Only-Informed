from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.orm import relationship

# Notes 
# for one-to-many relationships, use relationship() on the 'one' side 
#    backref creates a virtual column on the 'many' side to access the parent
# for one-to-one relationships
#    use relationship() with uselist=False to enforce one-to-one
# use db.Table to create a table without a model class
# for many-to-many relationships
#    use relationship() with 'secondary' parameter connecting to association table


@login_manager.user_loader # Flask-Login Decorator
def load_user(user_id):
    # Fetches user object from User table
    return User.query.get(int(user_id))

# User Entity - db.Model maps to database table, UserMixin is Flask-Login mixin
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    # define attributes, id = primary key 
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(128), nullable = False)

    # relationships 
    comments = relationship('Comment', backref = 'author', lazy = True)
    quizzes_passed = relationship('Quiz', secondary = 'user_quiz', backref = 'passed_users', lazy = 'dynamic')

    # defines string representation for User object 
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Article Entity 
class Article(db.Model):
    __tablename__ = 'article'

    # define attributes 
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    content = db.Column(db.Text, nullable = False)
    source = db.Column(db.String(200), nullable = False)
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
 
    # relationships 
    quiz = relationship('Quiz', uselist = False, backref = 'article') # uselist=false indicates a 1 to 1 relationship with quiz
    comments = relationship('Comment', backref = 'article', lazy = True)

    # string representation for Article object
    def __repr__(self):
        return f"Article('{self.title}', '{self.source}')"
    
# Quiz Entity
class Quiz(db.Model):
    __tablename__ = 'quiz'

    # attributes
    id = db.Column(db.Integer, primary_key = True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable = False)
    questions = db.Column(db.Text, nullable = False) # store as JSON string

    # string representation of Quiz object 
    def __repr__(self):
        return f"Quiz(Article ID: {self.article_id})"

# Comment Entity
class Comment(db.Model):
    __tablename__ = 'comment'

    # attributes
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text, nullable = False)
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable = False)


    # string representation of Comment object
    def __repr__(self):
        return f"Comment('{self.content[:20]}')"

# Association table for User <-> Quiz
# connects to user.id and quiz.id via foreign keys
user_quiz = db.Table('user_quiz', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key = True), 
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key = True), 
    db.Column('passed', db.Boolean, nullable = False, default = False)
)

