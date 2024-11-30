from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

#User table for login and registration
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    trips=db.relationship("PreviousTrips",backref='trip', cascade= "all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

#PreviousTrips table
class PreviousTrips(db.Model):
    __tablename__ = "trips"
    tripId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date_created = db.Column(db.Integer)
    itinerary = db.Column(db.String(30))
    #relationship between User table & trips table

    def __init__(self, tripId, User_id, date_created,itinerary):
        self.tripId = tripId
        self.User_id = User_id
        self.date_created = date_created
        self.itinerary=itinerary