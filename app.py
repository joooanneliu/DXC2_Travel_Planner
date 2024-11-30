import os
import serpapi
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta

from serpapi import GoogleSearch

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'  # Adjust to use the instance folder's db
app.config['SECRET_KEY'] = os.urandom(24)  # Needed for sessions
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'sign_in'  # Redirect users who are not logged in

migrate = Migrate(app, db)


# Airport Codes Dictionary
airport_codes = {
    "New York": "LGA",
    "Austin": "AUS",
    "San Francisco": "SFO",
    "Dallas": "DFW",
    "Chicago": "ORD",
    "Houston": "IAH"
}

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

        num_adults = request.form.get('adults', 0) 
        num_children = request.form.get('children', 0) 

        transport_mode = request.form.get('transport-mode')
        flight_needed = "Yes" if transport_mode == "Flight" else "No"
        car_needed = "Yes" if transport_mode == "Car" else "No"
        keywords = request.form.get('keywords', '')

        return redirect(url_for('confirmation', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                num_adults=num_adults,num_children=num_children,
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
    num_adults = request.args.get('num_adults')
    num_children = request.args.get('num_children')
    flight_needed = request.args.get('flight_needed')
    car_needed = request.args.get('car_needed')
    hotel_stars = request.args.get('hotel_stars')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')

    return render_template('confirmation.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                           num_adults=num_adults,num_children=num_children,
                           flight_needed=flight_needed, car_needed=car_needed,
                           hotel_stars=hotel_stars, budget=budget, keywords=keywords)

@app.route('/departure', methods=['GET', 'POST'])
@login_required
def departure():
    # Check if flight is needed
    flight_needed = request.args.get('flight_needed')
    if flight_needed == "No":
        return redirect(url_for('hotel'))

    # Retrieve data from query parameters
    start_date = request.args.get('start_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')

    
    departure_code = airport_codes.get(departure_city)
    arrival_code = airport_codes.get(arrival_city)

    params = {
        "engine": "google_flights",
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "outbound_date": start_date,
        "currency": "USD",
        "hl": "en",
        "api_key": "a780666c9c29631a90981f92043aabbd4ad07b787e71674ec474a4a07b7cdc15"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
   

    # Extract the first 4 best flights
    best_flights = results.get("best_flights", [])[:4]
    print(best_flights)
    # Render departure.html with the flight data
    return render_template('departure.html', flights=best_flights)

@app.route('/arrival', methods=['GET', 'POST'])
@login_required
def arrival():
    flight_needed = request.args.get('flight_needed')
    if flight_needed == "No":
        return redirect(url_for('hotel'))

    # Retrieve data from query parameters
    end_date = request.args.get('end_date')
    departure_city = request.args.get('arrival_city') 
    arrival_city = request.args.get('departure_city')

    # Map cities to their airport codes
    departure_code = airport_codes.get(departure_city)
    arrival_code = airport_codes.get(arrival_city)

    # Call SerpAPI for flight data (reverse the cities here)
    params = {
        "engine": "google_flights",
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "outbound_date": end_date,  # Use end_date as the flight date
        "currency": "USD",
        "hl": "en",
        "api_key": "your_api_key_here"
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    best_flights = results.get("best_flights", [])[:4]

    # Ensure 'best_flights' is being passed correctly
    return render_template('arrival.html', flights=best_flights)

# @app.route('/flightandcar')
# @login_required
# def flight_car():
#     return render_template('flight-car.html')

@app.route('/hotel', methods=['GET', 'POST'])
@login_required
def hotel():
    hotel_stars = request.args.get('hotel_stars', type=int) 
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    num_adults = request.args.get('num_adults')
    
    # Construct the hotel query based on the departure city
    hotel_query = f"{arrival_city} Resorts"
    
    # Call SerpAPI for hotel data
    params = {
        "engine": "google_hotels",
        "q": hotel_query,
        "check_in_date": start_date,
        "check_out_date": end_date,
        "adults": num_adults,
        "currency": "USD",
        "gl": "us",
        "hl": "en",
        "api_key": "your_api_key_here"
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    # Filter hotels based on the star rating
    hotels = results.get('properties', [])
    filtered_hotels = [hotel for hotel in hotels if hotel.get('overall_rating', 0) >= hotel_stars]

    # Get top 4 hotels
    top_hotels = filtered_hotels[:4]

    return render_template('hotel.html', hotels=top_hotels)

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
