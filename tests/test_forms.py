import unittest
from app import app
from app.forms import RegistrationForm

class FormTestCase(unittest.TestCase):
    # Initializes test environment before each test
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    # Tests the form with valid data, expected to pass validation
    def test_registration_form_valid_data(self):
        form = RegistrationForm(data={
            'username': 'validuser',
            'email': 'valid@example.com',
            'password': 'Validpass1!',
            'confirm_password': 'Validpass1!'
        })
        self.assertTrue(form.validate())

    # Tests the form with invalid data, expected to fail validation
    def test_registration_form_invalid_email(self):
        form = RegistrationForm(data={
            'username': 'user',
            'email': 'invalid-email',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertFalse(form.validate())
        self.assertIn('Invalid email address.', form.email.errors)

    # Tests the forms with mismatched passwords, expected to fail validation
    def test_registration_form_password_mismatch(self):
        form = RegistrationForm(data={
            'username': 'user',
            'email': 'user@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        })
        self.assertFalse(form.validate())
        self.assertIn('Field must be equal to password.', form.confirm_password.errors)

if __name__ == '__main__':
    unittest.main()