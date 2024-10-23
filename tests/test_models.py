import unittest
from app import app, db
from app.models import User, Article, Quiz, Comment
from datetime import datetime
import json

class ModelTestCase(unittest.TestCase):
    # Initializes test environment before each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    # 'Cleans up' after each test, removes the session and drops all tables in DB
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # Tests User object creation, saving, and retrieval 
    def test_user_creation(self):
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password='hashed_password')
            db.session.add(user)
            db.session.commit()
            retrieved_user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.email, 'test@example.com')

    # Tests Article object creation, saving, and retrieval
    def test_article_creation(self):
        with app.app_context():
            article = Article(title='Test Article', content='Content here.', source='https://example.com', date_posted=datetime.utcnow())
            db.session.add(article)
            db.session.commit()
            retrieved_article = Article.query.filter_by(title='Test Article').first()
            self.assertIsNotNone(retrieved_article)
            self.assertEqual(retrieved_article.source, 'https://example.com')

if __name__ == '__main__':
    unittest.main()