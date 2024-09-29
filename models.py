from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

#User table for login and registration
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

#Registration table
class Registration(db.Model):
    __tablename__ = "registrations"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)  # Storing hashed password
    login = db.relationship("Login", backref="registration", uselist=False)
    user_information = db.relationship("UserInformation", backref="registration", uselist=False)

    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = generate_password_hash(password)  # Hash the password

#Login table
class Login(db.Model):
    __tablename__ = "login"
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.Integer)
    destination_state = db.Column(db.String(10))
    pdf_link = db.Column(db.String(30))
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"))

    def __init__(self, date_created, destination_state, pdf_link):
        self.date_created = date_created
        self.destination_state = destination_state
        self.pdf_link = pdf_link

#UserInformation table
class UserInformation(db.Model):
    __tablename__ = "user_information"
    id = db.Column(db.Integer, primary_key=True)
    keywords_picked = db.Column(db.String(30))
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"))

    def __init__(self, keywords_picked):
        self.keywords_picked = keywords_picked
