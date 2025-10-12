import sys
sys.path.append('.')

from models.customer import Customer
from models import storage
from werkzeug.security import generate_password_hash

def create_test_user():
    print("Creating test user...")
    
    # Check if user already exists
    existing_users = storage.all(Customer)
    for user in existing_users.values():
        if user.email == 'test@example.com':
            print("Test user already exists!")
            return
    
    # Create new test user
    test_user = Customer(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        password=generate_password_hash('password123'),
        phone_number='1234567890'
    )
    
    test_user.save()
    print(f"Test user created with ID: {test_user.id}")
    print("Email: test@example.com")
    print("Password: password123")

if __name__ == "__main__":
    create_test_user()