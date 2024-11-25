import os
from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta
from openai import OpenAI
from dotenv import load_dotenv
from serpapi import GoogleSearch

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'  # Adjust to use the instance folder's db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
        # Get the form data from request.form
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        departure_city = request.form.get('departure-city')
        arrival_city = request.form.get('arrival-city')
        hotel_stars = request.form.get('hotel-stars')
        budget = request.form.get('budget')
        keywords = request.form.get('keywords', '')

        transport_mode = request.form.get('transport-mode')
        if transport_mode == "Flight":
            flight_needed = "Yes"
        else:
            flight_needed = "No"
        
        if  transport_mode == "Car":
            car_needed = "Yes"
        else:
            car_needed = "No"
        
        # Pass data directly to confirmation.html
        return redirect(url_for('confirmation', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                flight_needed=flight_needed, car_needed=car_needed,
                                hotel_stars=hotel_stars, budget=budget, keywords=keywords))
    
    # GET request to render the trip input form
    return render_template('trip-input.html')


@app.route('/confirmation', methods=["POST", "GET"])
@login_required
def confirmation():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    flight_needed = request.args.get('flight_needed')
    hotel_stars = request.args.get('hotel_stars')
    car_needed = request.args.get('car_needed')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')
    
    if request.method=="POST":
        return redirect(url_for('flightandcar', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                flight_needed=flight_needed, car_needed=car_needed,
                                hotel_stars=hotel_stars, budget=budget))
    

    return render_template('confirmation.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                           flight_needed=flight_needed, hotel_stars=hotel_stars,
                           car_needed=car_needed)

                           


@app.route('/flightdeparture')
@login_required
def flight_car_API_call():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')

    #departure flight call 
    params= { 
        "departure_id": departure_city,
        "arrival_id":arrival_city,
        "engine":'google_flights',
        "gl":"us",
        "hl": "en",
        "currency":"USD",
        #Advanced Google Flights parameters
        "type":"1",
        "outbound_date":start_date,
        "return_date": end_date,
        "adults":1,
        "children":0,
        "max_price":budget,
        "api_key": "serpAPI_key"

        }
    departureSearch= GoogleSearch(params)
    departureResults=departureSearch.get_dict()
    #grabbing flights entry in best flights list with 4 flights
    best_flights=departureResults["best_flights"][0]


    #arrival flight API call
    params= { 
        "departure_id": departure_city,
        "arrival_id":arrival_city,
        "engine":'google_flights',
        "gl":"us",
        "hl": "en",
        "currency":"USD",
        #Advanced Google Flights parameters
        "type":"1",
        "outbound_date":start_date,
        "return_date": end_date,
        "adults":1,
        "children":0,
        "max_price":budget,
        "api_key": "serpAPI_key"

        }
    arrivalSearch= GoogleSearch(params)
    arrivalResults=arrivalSearch.get_dict()

    return "Welcome to the flight and cars page. Please return "

@app.route('/flightarrival')
@login_required
def deaprtureflight():
    return "Welcome to the departure flight"

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

#OpenAI 
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

#SerpAPI
#serpAPI_key=os.getenv("OPENSERP_API_KEY")


@app.route('/generate-itinerary', methods=['GET'])
def generate_itinerary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    flight_needed = request.args.get('flight_needed')
    car_needed = request.args.get('car_needed')
    hotel_stars = request.args.get('hotel_stars')
    budget = request.args.get('budget')

    user_prompt = f"""
    Generate travel itinerary
    - Include timestamps, addresses of locations
    - Factor in travel time, especially to airport
    - List costs for each component; total budget only at the end
    - If renting a car, include rental details at the start
    Travel dates: from {start_date} to {end_date}
    Departure city: {departure_city}
    Arrival city: {arrival_city}
    Flight required: {flight_needed}
    Car rental required: {car_needed}
    Minimum hotel stars: {hotel_stars or "Not specified"}
    Budget level: {budget or "Not specified"}
    """

    # Generate response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    # Extract and return the text from OpenAI response
    itinerary = response.choices[0].message["content"]
    return jsonify({"itinerary": itinerary})

if __name__ == "__main__":
    app.run(debug=True)
