from flask import render_template, redirect, url_for, flash, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User, Article
from flask_login import login_user, current_user, logout_user, login_required

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # redirect user if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # initialize registration form
    form = RegistrationForm()

    # if form is submitted and valid, hash password and add to db
    if form.validate_on_submit():
        # hash password 
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # create user, add to database, and commit change to database
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        # success message and redirect
        flash('Your account has been created! You may now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title = 'Register', form=form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    # redirect user if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # initialize login form
    form = LoginForm()

    # if form is submitted and valid 
    if form.validate_on_submit():
        # grabs user based on provided email
        user = User.query.filter_by(email=form.email.data).first()

        # if user with provided email exists AND pasword matches
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # logs in user
            login_user(user, remember=form.remember.data)

            # redirects user to where they wanted to go
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title = "Login", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/articles')
def articles():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('articles.html', articles=articles)

@app.route('/article/<int:article_id>')
def article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article.html', article=article)