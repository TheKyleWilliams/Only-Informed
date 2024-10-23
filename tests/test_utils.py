import unittest
from app import app, bcrypt

class UtilsTestCase(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        password = 'SecurePass123!'
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.assertTrue(bcrypt.check_password_hash(hashed_password, password))
        self.assertFalse(bcrypt.check_password_hash(hashed_password, 'WrongPassword'))

if __name__ == '__main__':
    unittest.main()