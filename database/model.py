from datetime import time
from flask_login import UserMixin
from login.extensions import db  # Import db from extensions
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(100))
    attendances = db.relationship('Attendance', backref='volunteer', lazy=True)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.String(100), db.ForeignKey('volunteer.id'))
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    breakfast = db.Column(db.Boolean, default=False)
    lunch = db.Column(db.Boolean, default=False)
    dinner = db.Column(db.Boolean, default=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        logger.debug(
            f"Password hash set for user {self.username}: {self.password_hash}")

    def check_password(self, password):
        logger.debug(f"Checking password for user {self.username}")
        logger.debug(f"Stored password hash: {self.password_hash}")
        result = check_password_hash(self.password_hash, password)
        logger.debug(
            f"Password check result for user {self.username}: {result}")
        return result