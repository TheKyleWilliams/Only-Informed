from flask import render_template, redirect, url_for, flash, request
from app import app, db, bcrypt
#from app.forms import RegistrationForm, LoginForm
from app.models import User, Article
from flask_login import login_user, current_user, logout_user, login_required

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html', title = 'Register')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    return render_template('login.html', title = "Login")

@app.route('/articles')
def articles():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('articles.html', articles=articles)

@app.route('/article/<int:article_id>')
def article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article.html', article=article)