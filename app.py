import os
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'  # Adjust to use the instance folder's db
app.config['SECRET_KEY'] = os.urandom(24)  # Needed for sessions
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'sign_in'  # Redirect users who are not logged in

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Creating database tables (if not already existing)
with app.app_context():
    db.create_all()

# Flask Routes
@app.route('/')
def root():
    return redirect(url_for('sign_in'))


@app.route('/sign_in', methods=["POST", "GET"])
def sign_in():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('trip_input'))  
        else:
            flash('Login failed. Check email and password.', 'danger')
    return render_template('sign-in.html', form=form)

@app.route('/register', methods=["POST", "GET"])
def register():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('sign_in'))
    return render_template('register.html', form=form)

@app.route('/trip_input', methods=["POST", "GET"])
@login_required
def trip_input():
    if request.method == "POST":
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        departure_city = request.form.get('departure-city')
        arrival_city = request.form.get('arrival-city')
        hotel_stars = request.form.get('hotel-stars')
        budget = request.form.get('budget')

        transport_mode = request.form.get('transport-mode')
        flight_needed = "Yes" if transport_mode == "Flight" else "No"
        car_needed = "Yes" if transport_mode == "Car" else "No"
        keywords = request.form.get('keywords', '')

        return redirect(url_for('confirmation', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                flight_needed=flight_needed, car_needed=car_needed,
                                hotel_stars=hotel_stars, budget=budget, keywords=keywords))

    return render_template('trip-input.html')


@app.route('/confirmation')
@login_required
def confirmation():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    flight_needed = request.args.get('flight_needed')
    car_needed = request.args.get('car_needed')
    hotel_stars = request.args.get('hotel_stars')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')

    return render_template('confirmation.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                           flight_needed=flight_needed, car_needed=car_needed,
                           hotel_stars=hotel_stars, budget=budget, keywords=keywords)


@app.route('/flightandcar')
@login_required
def flight_car():
    return render_template('flight-car.html')

@app.route('/hotel')
@login_required
def hotel():
    return "Welcome to the hotel page"

@app.route('/itinerary')
@login_required
def itinerary():
    return "Welcome to the itinerary"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('sign_in'))

if __name__ == "__main__":
    app.run(debug=True)
