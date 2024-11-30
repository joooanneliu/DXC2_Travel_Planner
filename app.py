import os
from flask import Flask, render_template, url_for, redirect, request, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
import json
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

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")

client = OpenAI(api_key=api_key)

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


@app.route('/confirmation', methods=["POST", "GET"])
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
    return render_template('itinerary.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('sign_in'))


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

    if not all([start_date, end_date, departure_city, arrival_city, flight_needed, car_needed, hotel_stars, budget]):
        # Create an instance of FPDF
        pdf = FPDF()
        pdf.add_page()  # Add a blank page

        # Optional: Add minimal content, like a title or message
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Missing fields to generate itinerary", ln=True, align="C")

        # Output PDF as a binary response
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=blank_document.pdf'
        return response

    user_prompt = f"""Generate a detailed travel itinerary in JSON format. Ensure the itinerary includes all necessary details such as timestamps, addresses, travel durations, and costs. Use the following headers for the JSON structure:
    json headers: \"header\": \"departure_city\", \"arrival_city\", \"travel_dates\", \"car_rental_info\": \"company\", \"car_type\", \"pick_up_location\", \"pick_up_time\", \"return_location\", \"return_time\", \"total_price\", 
    \"content\": \"place\", \"location\", \"time_stamp\", \"description\", \"price\"\n
    Requirements: 
    1. Travel Dates: From {start_date} to {end_date}
    2. Departure City: {departure_city}
    3. Arrival City: {arrival_city}
    4. Flight Required: {flight_needed} - Outbound: DL1250, AUS to JFK, 4:03 PM to 8:59 PM, $368 - Return: DL1167, JFK to AUS, 1:13 PM to 4:25 PM
    5. Hotel Details: - Name: Hyatt Grand Central New York - Price: $2,589 
    6. Car Rental Required: {car_needed} - If renting a car, include rental details at the start of the itinerary under \"car_rental_info\". If not, leave \"car_rental_info\" as an empty object. 
    7. Budget Level: {budget or "Not specified"} 
    8. Additional Details: - Factor in travel time to/from the airport. 
    - Include descriptions of activities or places to visit in destination.
    - Provide a timestamp and detailed cost for each activity.
    - All numbers for prices"""

    # simple user prompt to test with
    # user_prompt = f'''return json object where json headers: \"header\": \"departure city\", \"arrival city\", \"travel dates\", \"car rental info\", \"content\": \"place\", \"location\", \"time stamp\", \"description\", \"price\"\n, one for header and car rental, two content items 
    # always number as a string for price'''

    # test link: http://127.0.0.1:5000/generate-itinerary?start_date=2024-12-01&end_date=2024-12-05&departure_city=New+York&arrival_city=Los+Angeles&flight_needed=yes&car_needed=yes&hotel_stars=4&budget=mid?action=view

    # Generate response from OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    # Response
    pdf_content_string = completion.choices[0].message.content
    pdf_content = json.loads(pdf_content_string)
    
    # Generate PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # # Add Header Section
    header = pdf_content['header']
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, "Travel Itinerary", ln=True, align='C')
    # pdf.multi_cell(0, 10, pdf_content_string)
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Departure City: {header['departure_city']}", ln=True)
    pdf.cell(0, 10, f"Arrival City: {header['arrival_city']}", ln=True)
    pdf.cell(0, 10, f"Travel Dates: From {header['travel_dates']['start_date']} to {header['travel_dates']['end_date']}", ln=True)
    pdf.ln(5)

    # Add Car Rental Info
    car_rental = header.get('car rental info', {})
    if car_rental:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "Car Rental Information:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"  Company: {car_rental.get('company', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Car Type: {car_rental.get('car_type', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Pickup Location: {car_rental.get('pickup_location', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Pickup Time: {car_rental.get('pickup_time', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Return Location: {car_rental.get('return_location', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Return Time: {car_rental.get('return_time', 'N/A')}", ln=True)
        pdf.ln(10)

    content_list = pdf_content.get('content', [])
    total_price = 0
    if content_list:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "Schedule:", ln=True)
        pdf.ln(5)
    
        for content in content_list:
            if isinstance(content, dict):  # Check if content is a dictionary
                price = content.get('price', '0')
                total_price += price
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"  Place: {content.get('place', 'N/A')}", ln=True)
                pdf.cell(0, 10, f"  Location: {content.get('location', 'N/A')}", ln=True)
                pdf.cell(0, 10, f"  Time Stamp: {content.get('time_stamp', 'N/A')}", ln=True)
                pdf.multi_cell(0, 10, f"  Description: {content.get('description', 'N/A')}")
                pdf.cell(0, 10, f"  Price: ${content.get('price', 'N/A')}", ln=True)
                pdf.ln(10)
            elif isinstance(content, str):  # Handle string content
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, f"  Note: {content}")
                pdf.ln(5)
    else:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "No destination information available.", ln=True)

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Total Price Summary:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"  Total Price: ${total_price}", ln=True)
    pdf.ln(10)

    # Determine if the PDF should be downloaded or displayed inline
    disposition = "inline" if request.args.get("action") == "view" else "attachment"

    # Create a response with the PDF
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'{disposition}; filename=itinerary.pdf'

    return response

if __name__ == "__main__":
    app.run(debug=True)
