import openai
import os
import json
from app.models import Quiz, Article
from app import db
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

def clean_quiz_text(quiz_text):
    # Removes code fencing and extra characters from the quiz_text.
    # Remove code fencing if present
    if quiz_text.startswith("```") and quiz_text.endswith("```"):
        # Split by newlines and ignore the first and last lines
        lines = quiz_text.strip().split('\n')
        if len(lines) >= 3:
            quiz_text = '\n'.join(lines[1:-1])
    
    # Strip leading/trailing whitespace
    return quiz_text.strip()

def generate_quiz(article_id, retries=3, delay=5):
    # Retrieve the article from the database
    article = Article.query.get(article_id)
    if not article:
        logger.error(f"Article ID {article_id} not found.")
        return None  # Or handle the error as needed

    # Design the prompt
    prompt = f"""
    Read the following article and generate a 5-question multiple-choice quiz to test the reader's understanding of the content. Each question should have one correct answer and three plausible distractors. Ensure that the response is valid JSON without markdown or code fencing.

    Format:
    [
        {{
            "question": "Question text",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A"
        }},
        ...
    ]

    Article:
    {article.content}
    """

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that generates quiz questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            quiz_text = response['choices'][0]['message']['content'].strip()
            quiz_text = clean_quiz_text(quiz_text)
            logger.info(f"Raw quiz_text for Article ID {article_id}: {quiz_text}")

            try:
                quiz_questions = json.loads(quiz_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for Article ID {article_id}: {e}")
                logger.error(f"Received quiz_text: {quiz_text}")
                return None

            if not isinstance(quiz_questions, list):
                logger.error(f"Quiz JSON is not a list for Article ID {article_id}")
                return None

            for q in quiz_questions:
                if not all(k in q for k in ("question", "options", "correct_answer")):
                    logger.error(f"Quiz JSON missing fields for Article ID {article_id}: {q}")
                    return None
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    logger.error(f"Quiz options not valid for Article ID {article_id}: {q}")
                    return None

            # Create a new Quiz object but DO NOT commit here
            quiz = Quiz(
                article_id=article.id,
                questions=json.dumps(quiz_questions)
            )

            logger.info(f"Successfully generated quiz object for Article ID {article_id}")
            return quiz

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error on attempt {attempt + 1} for Article ID {article_id}: {e}")
            logger.error(f"Received quiz_text: {quiz_text}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed after {retries} attempts for Article ID {article_id}")
                return None
        except Exception as e:
            logger.error(f"Error generating quiz for Article ID {article_id}: {e}")
            db.session.rollback()  # Rollback if something failed
            return None