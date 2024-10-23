import unittest
from app import app, db, bcrypt
from app.models import User
from time import time

class PerformanceTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a test user
            password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
            user = User(username='testuser', email='test@example.com', password=password_hash)
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_multiple_logins(self):
        start_time = time()
        login_attempts = 100
        for _ in range(login_attempts):
            response = self.app.post('/login', data=dict(
                email='test@example.com',
                password='password'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'You have been logged in!', response.data)
        end_time = time()
        duration = end_time - start_time
        print(f'Time taken for {login_attempts} login attempts: {duration:.2f} seconds')

if __name__ == '__main__':
    unittest.main()