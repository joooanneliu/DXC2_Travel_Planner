import os

import json
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta
from openai import OpenAI
from fpdf import FPDF
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

        # Validation
        if not start_date or not end_date or departure_city == "default" or arrival_city == "default":
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for('trip_input'))

        return redirect(url_for('confirmation', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                num_adults=num_adults, num_children=num_children,
                                flight_needed=flight_needed, car_needed=car_needed,
                                hotel_stars=hotel_stars, budget=budget, keywords=keywords))

    return render_template('trip-input.html')


@app.route('/confirmation')
@login_required
def confirmation():
    # Retrieve query parameters using the correct names
    start_date = request.args.get('start-date')
    end_date = request.args.get('end-date')
    departure_city = request.args.get('departure-city')
    arrival_city = request.args.get('arrival-city')
    num_adults = request.args.get('adults', 1)  # Default to 1 adult
    num_children = request.args.get('children', 0)  # Default to 0 children
    flight_needed = request.args.get('transport-mode', "No")  # Based on transport mode
    flight_needed = "Yes" if flight_needed == "Flight" else "No"
    car_needed = "Yes" if flight_needed == "Car" else "No"
    hotel_stars = request.args.get('hotel-stars', 2)
    budget = request.args.get('budget', "default")
    keywords = request.args.get('keywords', "")

    # Determine the next route based on flight_needed
    next_route = 'departure' if flight_needed == "Yes" else 'hotel'

    # Debugging
    print(f"Start Date: {start_date}, End Date: {end_date}")
    print(f"Departure City: {departure_city}, Arrival City: {arrival_city}")
    print(f"Flight Needed: {flight_needed}, Car Needed: {car_needed}")
    print(f"Next Route: {next_route}")

    # Validation
    if not start_date or not end_date or not departure_city or not arrival_city:
        flash("Missing required travel details. Please start over.", "warning")
        return redirect(url_for('trip_input'))

    return render_template('confirmation.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                           num_adults=num_adults, num_children=num_children,
                           flight_needed=flight_needed, car_needed=car_needed,
                           hotel_stars=hotel_stars, budget=budget, keywords=keywords,
                           next_route=next_route)




@app.route('/departure', methods=['GET', 'POST'])
@login_required
def departure():
    # Retrieve query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date') or "2025-05-10"  # Default if not provided
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    num_adults = request.args.get('num_adults') or 1  # Default to 1 adult if missing
    num_children = request.args.get('num_children') or 0  # Default to 0 children if missing
    hotel_stars = request.args.get('hotel_stars') or 2
    budget = request.args.get('budget', "default")
    keywords = request.args.get('keywords', "").strip()
    flight_needed = request.args.get('flight_needed', "Yes")
    car_needed = request.args.get('car_needed', "No")

    # Map to airport codes
    departure_code = airport_codes.get(departure_city)
    arrival_code = airport_codes.get(arrival_city)

    if not departure_code or not arrival_code:
        flash("Invalid city selection. Please try again.", "warning")
        return redirect(url_for('trip_input'))

    # SerpAPI query parameters
    params = {
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "engine": "google_flights",
        "gl": "us",
        "hl": "en",
        "currency": "USD",
        "type": "2",  # One-way flight
        "outbound_date": start_date,
        "adults": num_adults,
        "children": num_children,
        "stops": 1,  # Limit to direct flights
        "api_key": "a780666c9c29631a90981f92043aabbd4ad07b787e71674ec474a4a07b7cdc15"
    }

    # Call SerpAPI
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        flights = results.get("best_flights", [])
        print(f"API Response for Departure Flights: {results}")  # Debugging
    except Exception as e:
        print(f"Error during SerpAPI call: {e}")
        flash("Failed to fetch departure flights. Please try again later.", "warning")
        flights = []

    # Format flights for display
    outbound_flights = [
        {
            "price": flight['price'],
            "departure_airport": flight['flights'][0]['departure_airport']['name'],
            "departure_time": flight['flights'][0]['departure_airport']['time'],
            "arrival_airport": flight['flights'][0]['arrival_airport']['name'],
            "arrival_time": flight['flights'][0]['arrival_airport']['time']
        }
        for flight in flights
    ]

    # Render the departure page
    return render_template(
        'departure.html',
        flights=outbound_flights,
        start_date=start_date,
        end_date=end_date,
        departure_city=departure_city,
        arrival_city=arrival_city,
        num_adults=num_adults,
        num_children=num_children,
        hotel_stars=hotel_stars,
        budget=budget,
        keywords=keywords,
        flight_needed=flight_needed,
        car_needed=car_needed
    )



@app.route('/arrival', methods=['GET', 'POST'])
@login_required
def arrival():
    # Retrieve query parameters
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')  # Pass through to the next step
    departure_city = request.args.get('arrival_city')  # Reverse mapping
    arrival_city = request.args.get('departure_city')  # Reverse mapping
    num_adults = request.args.get('num_adults') or 1  # Default to 1 adult if not provided
    num_children = request.args.get('num_children') or 0  # Default to 0 children if not provided
    hotel_stars = request.args.get('hotel_stars') or 2
    budget = request.args.get('budget', "default")
    flight_needed = request.args.get('flight_needed', "Yes")
    car_needed = request.args.get('car_needed', "No")
    keywords = request.args.get('keywords', "").strip()

    # Map to airport codes
    departure_code = airport_codes.get(departure_city)
    arrival_code = airport_codes.get(arrival_city)

    if not departure_code or not arrival_code:
        flash("Invalid city selection for return flight.", "warning")
        return redirect(url_for('departure'))  # Redirect to departure if cities are invalid

    # SerpAPI query parameters
    params = {
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "engine": "google_flights",
        "gl": "us",
        "hl": "en",
        "currency": "USD",
        "type": "2",  # One-way flight
        "outbound_date": end_date,
        "adults": num_adults,
        "children": num_children,
        "stops": 1,  # Only direct flights
        "api_key": "a780666c9c29631a90981f92043aabbd4ad07b787e71674ec474a4a07b7cdc15"
    }

    print(f"Arrival Params: {params}")  # Debugging
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"Arrival API Response: {results}")  # Debugging
        flights = results.get("best_flights", [])
    except Exception as e:
        print(f"Error during SerpAPI call: {e}")
        flash("Failed to fetch return flights. Please try again.", "warning")
        flights = []

    # Format flights for display
    inbound_flights = [
        {
            "price": flight['price'],
            "departure_airport": flight['flights'][0]['departure_airport']['name'],
            "departure_time": flight['flights'][0]['departure_airport']['time'],
            "arrival_airport": flight['flights'][0]['arrival_airport']['name'],
            "arrival_time": flight['flights'][0]['arrival_airport']['time']
        }
        for flight in flights
    ]

    # Render the arrival page
    return render_template(
        'arrival.html',
        flights=inbound_flights,
        end_date=end_date,
        start_date=start_date,
        departure_city=departure_city,
        arrival_city=arrival_city,
        num_adults=num_adults,
        num_children=num_children,
        hotel_stars=hotel_stars,
        budget=budget,
        flight_needed=flight_needed,
        car_needed=car_needed,
        keywords=keywords
    )


@app.route('/hotel', methods=['GET', 'POST'])
@login_required
def hotel():
    # Retrieve parameters from query args
    hotel_stars = request.args.get('hotel_stars', type=int) or 2  # Default to 2 stars
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    num_adults = request.args.get('num_adults') or 1  # Default to 1 adult
    num_children = request.args.get('num_children') or 0  # Default to 0 children
    budget = request.args.get('budget', "default")
    flight_needed = request.args.get('flight_needed', "Yes")
    car_needed = request.args.get('car_needed', "No")
    keywords = request.args.get('keywords', "").strip()
    

    # Validate and ensure `arrival_city` is used for hotel search
    if not arrival_city or arrival_city == departure_city:
        arrival_city = request.args.get('final_arrival_city', departure_city)

    # Construct the hotel query based on the `arrival_city`
    hotel_query = f"{arrival_city} Resorts"

    # Debugging
    print(f"Hotel Query: {hotel_query}")
    print(f"Search Parameters: Hotel Stars: {hotel_stars}, Start Date: {start_date}, End Date: {end_date}")

    # Call SerpAPI for hotel data
    params = {
        "engine": "google_hotels",
        "q": hotel_query,
        "check_in_date": start_date,
        "check_out_date": end_date,
        "adults": num_adults,
        "children": num_children,
        "currency": "USD",
        "hotel_class": hotel_stars,
        "gl": "us",
        "hl": "en",
        "api_key": "a780666c9c29631a90981f92043aabbd4ad07b787e71674ec474a4a07b7cdc15"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        hotels = results.get('properties', [])
        print(json.dumps(hotels, indent=4))  # Debugging the full API response
    except Exception as e:
        print(f"Error fetching hotels: {e}")
        flash("Failed to fetch hotel data. Please try again later.", "warning")
        hotels = []

    # Extract and format hotel details
    filtered_hotels = [
        # {
        #     "name": hotel.get('name'),
        #     "overall_rating": hotel.get('overall_rating'),
        #     "rate_per_night": hotel.get('rate_per_night', {}).get('lowest') or hotel.get('price') or "N/A",
        #     "hotel_class": hotel.get('hotel_class', "N/A"),
        #     "images": hotel.get('images', [{"thumbnail": ""}])
        # }
        hotel for hotel in hotels
        if hotel.get('overall_rating') is not None
    ]

    # Limit to top 4 hotels
    top_hotels = filtered_hotels[:4]

    # Render the hotel selection page
    return render_template(
        'hotel.html',
        hotels=top_hotels,
        start_date=start_date,
        end_date=end_date,
        departure_city=departure_city,
        arrival_city=arrival_city,
        num_adults=num_adults,
        num_children=num_children,
        hotel_stars=hotel_stars,
        budget=budget,
        car_needed=car_needed,
        flight_needed=flight_needed,
        keywords=keywords
    )



@app.route('/itinerary', methods=['GET', 'POST'])
@login_required
def itinerary():
    return render_template('itinerary.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('sign_in'))

if __name__ == "__main__":
    app.run(debug=True)
