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
    
    # Design the prompt with escaped braces
    prompt = f"""
    Read the following article and generate a 5-question multiple-choice quiz to test the reader's understanding of the content. Each question should have one correct answer and three plausible distractors. Ensure that the response is valid JSON **without any markdown, code fencing, or additional text**.

    Format the quiz as a JSON array of objects, each containing the following fields:
    - "question": The quiz question.
    - "options": An array of four answer options.
    - "correct_answer": The correct answer string.

    Example:
    [
        {{
            "question": "What is the capital of France?",
            "options": ["Paris", "London", "Rome", "Berlin"],
            "correct_answer": "Paris"
        }},
        ...
    ]

    Article:
    {article.content}
    """

    # attemps api call three times with a delay to avoid api errors
    for attempt in range(retries):
        try:
            # API Call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "gpt-4" if available
                messages=[
                    {"role": "system", "content": "You are an AI that generates quiz questions based on provided articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                stop=["\n\n"]  # To prevent chatgpt from adding extra text after JSON
            )
            
            # Extract quiz text from API response
            quiz_text = response['choices'][0]['message']['content'].strip()

            # Clean the quiz_text
            quiz_text = clean_quiz_text(quiz_text)

            # Log the raw quiz_text for debugging purposes
            logger.info(f"Raw quiz_text for Article ID {article_id}: {quiz_text}")


            # Parse the JSON response
            try:
                quiz_questions = json.loads(quiz_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for Article ID {article_id}: {e}")
                logger.error(f"Received quiz_text: {quiz_text}")
                print(f"Failed to parse quiz JSON for Article ID {article_id}")
                return None

            # Checks that API response is a python list as specified
            if not isinstance(quiz_questions, list):
                logger.error(f"Quiz JSON is not a list for Article ID {article_id}")
                raise ValueError("Quiz JSON is not a list.")

            for q in quiz_questions:
                # Ensures that quiz_questions list is in the right format with a question, options, and corrrect_answer
                if not all(k in q for k in ("question", "options", "correct_answer")):
                    logger.error(f"Quiz JSON missing fields in Article ID {article_id}: {q}")
                    raise ValueError("Quiz JSON missing required fields.")
                # Checks that options is a list and has exactly 4 options
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    logger.error(f"Quiz options are not a list of four in Article ID {article_id}: {q}")
                    raise ValueError("Quiz options are not a list of four.")

            # Create a new Quiz object
            quiz = Quiz(
                article_id=article.id,
                questions=json.dumps(quiz_questions)  # Store as JSON string
            )

            # commit and add to database
            db.session.add(quiz)
            db.session.commit()

            logger.info(f"Successfully added quiz for Article ID {article_id}")
            return quiz

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error on attempt {attempt + 1} for Article ID {article_id}: {e}")
            logger.error(f"Received quiz_text: {quiz_text}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to parse quiz JSON for Article ID {article_id} after {retries} attempts.")
                return None
        except ValueError as e:
            logger.error(f"Validation error for Article ID {article_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating quiz for Article ID {article_id}: {e}")
            print(f"Error generating quiz for Article ID {article_id}: {e}")
            return None
        