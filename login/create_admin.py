from login.extensions import db
from database.model import User
from app import app


def create_admin(username, password):
    with app.app_context():
        db.create_all()
        admin = User(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {username} created successfully.')


if __name__ == '__main__':
    username = input('Enter admin username: ')
    password = input('Enter admin password: ')
    create_admin(username, password)
