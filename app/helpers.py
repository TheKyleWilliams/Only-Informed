from venv import logger
from app.models import UserQuiz, Quiz
from app import db

def user_has_passed_quiz(user_id, article_id):
    # grab quiz for associated article
    quiz = Quiz.query.filter_by(article_id = article_id).first()
    
    # check that quiz exists
    if not quiz:
        logger.info(f"No quiz found for Article ID {article_id}")
        return False
    
    # query user_quiz table to see if the user has passed the quiz
    user_quiz_entry = UserQuiz.query.filter_by(user_id=user_id, quiz_id=quiz.id).first()

    if user_quiz_entry and user_quiz_entry.passed:
        logger.info(f"User {user_id} has passed quiz {quiz.id}")
        return True
    
    logger.info(f"User {user_id} has not passed quiz {quiz.id}")
    return False


def user_has_attempted_quiz(user_id, article_id):
    quiz = Quiz.query.filter_by(article_id=article_id).first()
    if not quiz:
        return False

    user_quiz_entry = UserQuiz.query.filter_by(
        user_id=user_id,
        quiz_id=quiz.id
    ).first()

    return user_quiz_entry is not None and user_quiz_entry.attempted