from datetime import datetime, timezone
import json
import logging  # Import the standard logging module
from flask import render_template, jsonify, abort, redirect, url_for, flash, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User, Article, Quiz, Comment, UserQuiz  # Updated import
from app.quiz_generator import generate_quiz
from app.helpers import user_has_passed_quiz, user_has_attempted_quiz
from flask_login import login_user, current_user, logout_user, login_required

# Initialize logger
logger = logging.getLogger('app')

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

################################################
#   User Authentication Flow
################################################
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
    
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
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

        # if user with provided email exists AND password matches
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
    return render_template('login.html', title="Login", form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

################################################
#   Articles
################################################
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
    
    generated_quiz = None
    if not quiz:
        logger.info(f"Article ID {article_id}: No quiz found. Generating quiz...")
        generated_quiz = generate_quiz(article_id)
        if generated_quiz:
            db.session.add(generated_quiz)
            try:
                db.session.commit()
                quiz = generated_quiz
            except Exception as e:
                db.session.rollback()
                logger.error(f"Could not commit new quiz for Article {article_id}: {e}")
                return render_template('article.html', article=article, quiz=None, quiz_attempted=False, quiz_passed=False, saved_score=None, saved_feedback=[])
        else:
            # If generated_quiz is None, we failed to create a quiz
            logger.error(f"Article ID {article_id}: Failed to generate quiz.")
            return render_template('article.html', article=article, quiz=None, quiz_attempted=False, quiz_passed=False, saved_score=None, saved_feedback=[])
    
    quiz_questions = None
    quiz_attempted = False
    quiz_passed = False
    saved_score = None
    saved_feedback = []

    user_quiz_entry = None
    if quiz:
        # creates UserQuiz object
        user_quiz_entry = UserQuiz.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz.id
        ).first()

        quiz_attempted = user_quiz_entry.attempted if user_quiz_entry else False
        quiz_passed = user_quiz_entry.passed if user_quiz_entry else False

        # If user_quiz_entry has results saved
        if user_quiz_entry and user_quiz_entry.results_json:
            try:
                saved_feedback = json.loads(user_quiz_entry.results_json)
            except json.JSONDecodeError:
                saved_feedback = []
            saved_score = user_quiz_entry.score

        # If user hasn't attempted or passed yet, show quiz questions
        if not quiz_attempted and not quiz_passed:
            try:
                quiz_questions = json.loads(quiz.questions)
                logger.info(f"Article ID {article_id}: Parsed quiz_questions successfully.")
            except json.JSONDecodeError as e:
                logger.error(f"Article ID {article_id}: Invalid JSON in quiz.questions - {e}")
                quiz_questions = None

    # Render the template with the parsed quiz_questions and saved results
    return render_template('article.html', 
                           article=article, 
                           quiz=quiz, 
                           quiz_questions=quiz_questions, 
                           quiz_attempted=quiz_attempted, 
                           quiz_passed=quiz_passed,
                           saved_score=saved_score,
                           saved_feedback=saved_feedback)

################################################
#   Quiz Generation / Submission
################################################
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
        return jsonify({'status': 'failure', 'message': 'Invalid data.'}), 200

    # Retrieve the quiz for the article
    quiz = Quiz.query.filter_by(article_id=article_id).first()
    if not quiz:
        logger.error(f"No quiz found for Article ID {article_id}.")
        return jsonify({'status': 'failure', 'message': 'Quiz not found.'}), 200

    try:
        # Parse the quiz questions into a list
        quiz_questions = json.loads(quiz.questions)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in quiz.questions for Article ID {article_id}: {e}")
        return jsonify({'status': 'failure', 'message': 'Quiz data corrupted.'}), 200

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

    # Determine if the user passed
    passing_score = 5 
    passed = score >= passing_score
    logger.info(f"User {current_user.id} scored {score}/{total}. Passed: {passed}")

    # Update the user_quiz table using UserQuiz model
    user_quiz_entry = UserQuiz.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id
    ).first()

    if user_quiz_entry:
        user_quiz_entry.passed = passed
        user_quiz_entry.attempted = True
        user_quiz_entry.score = score
        user_quiz_entry.results_json = json.dumps(feedback)  # Store feedback as JSON
        logger.info(f"Updated UserQuiz entry for User ID {current_user.id} and Quiz ID {quiz.id} to Passed: {passed}, Score: {score}")
    else:
        user_quiz_entry = UserQuiz(
            user_id=current_user.id,
            quiz_id=quiz.id,
            attempted=True,
            passed=passed,
            score=score,
            results_json=json.dumps(feedback)
        )
        db.session.add(user_quiz_entry)
        logger.info(f"Created new UserQuiz entry for User ID {current_user.id} and Quiz ID {quiz.id} with Passed: {passed}, Score: {score}")

    db.session.commit()

    status = 'success' if passed else 'failure'
    message = 'Quiz passed.' if passed else 'Quiz not passed.'

    return jsonify({
        'status': status,
        'score': score,
        'total': total,
        'feedback': feedback,
        'message': message
    }), 200

################################################
#   Commenting
################################################
@app.route('/article/<int:article_id>/comment', methods=['POST'])
@login_required
def post_comment(article_id):
    # grab article from DB
    article = Article.query.get_or_404(article_id)

    # grab comment from form
    content = request.form.get('content')

    # comment validation
    if not content or content.strip() == '':
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('article', article_id=article_id))
    
    # access control: must pass quiz to comment
    if not user_has_passed_quiz(current_user.id, article_id):
        flash('You must pass the quiz to comment', 'warning')
        return redirect(url_for('article', article_id=article_id))

    # create and save comment to DB
    comment = Comment(content=content, author=current_user, article=article)
    db.session.add(comment)
    db.session.commit()

    flash('Your comment has been posted!', 'success')
    return redirect(url_for('article', article_id=article_id))

@app.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    # get comment from DB
    comment = Comment.query.get_or_404(comment_id)

    # validate that current user is comment author
    if comment.author != current_user:
        flash('You do not have permission to edit this comment')
        return redirect(url_for('article', article_id=comment.article_id))
    
    # post updated comment
    if request.method == 'POST':
        # get comment from form
        content = request.form.get('content')

        # validate comment
        if not content or content.strip() == '':
            flash('Comment cannot be empty', 'danger')
            return redirect(url_for('edit_comment', comment_id=comment_id))
        
        # update comment changes to db
        comment.content = content
        comment.date_posted = datetime.now(timezone.utc)
        db.session.commit()

        flash('Your comment has been updated!', 'success')
        return redirect(url_for('article', article_id=comment.article_id))

    return render_template('edit_comment.html', comment=comment)

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    # get comment from DB
    comment = Comment.query.get_or_404(comment_id)

    if current_user != comment.author:
        flash('You do not have permission to delete this comment', 'danger')
        return redirect(url_for('article', article_id=comment.article_id))
    
    # delete comment from DB
    db.session.delete(comment)
    db.session.commit()

    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('article', article_id=comment.article_id))