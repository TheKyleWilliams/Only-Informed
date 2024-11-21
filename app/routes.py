import json
from venv import logger
from flask import render_template, jsonify, abort, redirect, url_for, flash, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User, Article, Quiz
from app.quiz_generator import generate_quiz
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

            # flask success
            flash('Login successful', 'success')

            # redirects user to where they wanted to go
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title = "Login", form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/articles')
def articles():
    # grabs page parameter, default = 1 if none is provided
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('articles.html', articles=articles)

@app.route('/article/<int:article_id>', methods=['GET'])
@login_required
def article(article_id):
    # Retrieve the article
    article = Article.query.get_or_404(article_id)
    
    # Retrieve the associated quiz
    quiz = Quiz.query.filter_by(article_id=article_id).first()
    
    # generates quiz if one doesn't already exist
    if not quiz:
        logger.info(f"Article ID {article_id}: No quiz found. Generating quiz...")
        quiz = generate_quiz(article_id)
        if not quiz:
            logger.error(f"Article ID {article_id}: Failed to generate quiz.")
    
    if quiz:
        try:
            # Parse the JSON string into a Python list
            quiz_questions = json.loads(quiz.questions)
            logger.info(f"Article ID {article_id}: Parsed quiz_questions successfully.")
        except json.JSONDecodeError as e:
            logger.error(f"Article ID {article_id}: Invalid JSON in quiz.questions - {e}")
            quiz_questions = None
    else:
        quiz_questions = None
    
    # Log whether quiz_questions is available
    if quiz_questions:
        logger.info(f"Article ID {article_id}: Quiz is available with {len(quiz_questions)} questions.")
    else:
        if quiz:
            logger.error(f"Article ID {article_id}: Quiz exists but questions could not be loaded.")
        else:
            logger.info(f"Article ID {article_id}: No quiz available.")
    
    # Render the template with the parsed quiz_questions
    return render_template('article.html', article=article, quiz=quiz, quiz_questions=quiz_questions)

@app.route('/generate_quiz/<int:article_id>', methods=['POST'])
@login_required
def generate_quiz_route(article_id):
    # generate quiz
    quiz = generate_quiz(article_id)

    # successful generation
    if quiz:
        return jsonify({
            'status': 'success',
            'quiz_id': quiz.id,
            'questions': quiz.questions
        }), 200
    # unsuccessful generation
    else:
        return jsonify({
            'status': 'failure', 
            'message': 'Quiz generation failed'
        }), 500
    
@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    # grabs data sent to backend
    data = request.get_json()
    article_id = data.get('article_id')
    responses = data.get('responses')

    # error with sent data
    if not article_id or not responses:
        logger.error("Invalid data received: Missing article_id or responses.")
        return jsonify({'status': 'failure', 'message': 'Invalid data.'}), 400

    # Retrieve the quiz for the article
    quiz = Quiz.query.filter_by(article_id=article_id).first()
    if not quiz:
        logger.error(f"No quiz found for Article ID {article_id}.")
        return jsonify({'status': 'failure', 'message': 'Quiz not found.'}), 404

    try:
        # Parse the quiz questions into a list
        quiz_questions = json.loads(quiz.questions)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in quiz.questions for Article ID {article_id}: {e}")
        return jsonify({'status': 'failure', 'message': 'Quiz data corrupted.'}), 500

    # initialize scoring variables
    score = 0
    total = len(quiz_questions)
    feedback = []

    # score quiz results
    for i, question in enumerate(quiz_questions):
        q_text = question.get('question')
        correct_answer = question.get('correct_answer')
        user_answer = responses.get(f'question_{i}')
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        feedback.append({
            'question': q_text,
            'your_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })

    return jsonify({
        'status': 'success',
        'score': score,
        'total': total,
        'feedback': feedback
    }), 200