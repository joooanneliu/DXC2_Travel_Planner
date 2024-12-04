import os
import json
import openai
from flask import Flask, render_template, url_for, redirect, request, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupForm
from models import db, User
from flask_migrate import Migrate
from datetime import timedelta, datetime
from fpdf import FPDF
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
serpAPI_key = os.getenv("SERP_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    transportMode = request.args.get('transport-mode', "No")  # Based on transport mode
    flight_needed = "Yes" if transportMode == "Flight" else "No"
    car_needed = "Yes" if transportMode == "Car" else "No"
    hotel_stars = request.args.get('hotel-stars', 2)
    budget = request.args.get('budget', "default")
    keywords = request.args.get('keywords', "")

    # Determine the next route based on flight_needed
    next_route = 'departure' if flight_needed == "Yes" else 'hotel'

    # Debugging
    # print(f"Start Date: {start_date}, End Date: {end_date}")
    # print(f"Departure City: {departure_city}, Arrival City: {arrival_city}")
    # print(f"Flight Needed: {flight_needed}, Car Needed: {car_needed}")
    # print(f"Next Route: {next_route}")

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
        "api_key": serpAPI_key
    }

    # Call SerpAPI
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        flights = results.get("best_flights", [])
       # print(f"API Response for Departure Flights: {results}")  # Debugging
    except Exception as e:
        print(f"Error during SerpAPI call: {e}")
        flash("Failed to fetch departure flights. Please try again later.", "warning")
        flights = []

    # Format flights for display
    outbound_flights = [
        {
            "price": flight['price'],
            "flight_number": flight['flights'][0]['flight_number'],
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
        "api_key": serpAPI_key
    }

    #print(f"Arrival Params: {params}")  # Debugging
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        #print(f"Arrival API Response: {results}")  # Debugging
        flights = results.get("best_flights", [])
    except Exception as e:
        print(f"Error during SerpAPI call: {e}")
        flash("Failed to fetch return flights. Please try again.", "warning")
        flights = []

    # Format flights for display
    inbound_flights = [
        {
            "price": flight['price'],
            "flight_number": flight['flights'][0]['flight_number'],
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
        departure_city=arrival_city,
        arrival_city=departure_city,
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
    # print(f"Hotel Query: {hotel_query}")
    # print(f"Search Parameters: Hotel Stars: {hotel_stars}, Start Date: {start_date}, End Date: {end_date}")

    # Call SerpAPI for hotel data
    params = {
        "engine": "google_hotels",
        "q": hotel_query,
        "check_in_date": start_date,
        "check_out_date": end_date,
        "adults": num_adults,
        "children": 0,
        "currency": "USD",
        "hotel_class": hotel_stars,
        "gl": "us",
        "hl": "en",
        "api_key": serpAPI_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        hotels = results.get('properties', [])
        # print(json.dumps(hotels, indent=4))  # Debugging the full API response
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
    # Collect parameters passed through GET or POST
    params = {
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "departure_city": request.args.get("departure_city"),
        "arrival_city": request.args.get("arrival_city"),
        "flight_needed": request.args.get("flight_needed"),
        "car_needed": request.args.get("car_needed"),
        "hotel_stars": request.args.get("hotel_stars"),
        "budget": request.args.get("budget"),
        "keywords": request.args.get("keywords"),
        "num_adults": request.args.get("num_adults"),
        "num_children": request.args.get("num_children"),
        "departing_flight": request.args.get("departing_flight"),
        "returning_flight": request.args.get("returning_flight"),
        "hotel": request.args.get("hotel"),
    }

    #print("Itinerary parameters:", json.dumps(params, indent=4))
    return render_template('itinerary.html', **params)

@app.route('/generate-itinerary', methods=['GET'])
def generate_itinerary():
    # Standard details
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    flight_needed = request.args.get('flight_needed')
    car_needed = request.args.get('car_needed')
    hotel_stars = request.args.get('hotel_stars')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords', '')
    num_adults = request.args.get('num_adults') or 1  # Default to 1 adult if not provided
    num_children = request.args.get('num_children') or 0  # Default to 0 children 


    # Parse departing flight
    departing_flight_data = request.args.get('departing_flight')
    departing_flight = {}
    if departing_flight_data:
        departing_flight_details = departing_flight_data.split('|')
        if len(departing_flight_details) >= 6:
            departing_flight = {
                "price": departing_flight_details[0],
                "flight_number": departing_flight_details[1],
                "departure_airport": departing_flight_details[2],
                "departure_time": departing_flight_details[3],
                "arrival_airport": departing_flight_details[4],
                "arrival_time": departing_flight_details[5]
            }
        else:
            flash("Invalid departing flight details.", "warning")

    # Parse returning flight
    returning_flight_data = request.args.get('returning_flight')
    returning_flight = {}
    if returning_flight_data:
        returning_flight_details = returning_flight_data.split('|')
        if len(returning_flight_details) >= 5:
            returning_flight = {
                "price": returning_flight_details[0],
                "flight_number": returning_flight_details[1],
                "departure_airport": returning_flight_details[2],
                "departure_time": returning_flight_details[3],
                "arrival_airport": returning_flight_details[4],
                "arrival_time": returning_flight_details[5]
            }
        else:
            flash("Invalid returning flight details.", "warning")

    # Parse selected hotel
    selected_hotel = request.args.get('hotel')
    hotel = {}
    if selected_hotel:
        hotel_details = selected_hotel.split('|')
        if len(hotel_details) >= 3:
            hotel = {
                "name": hotel_details[0],
                "price_per_night": hotel_details[1],
                "rating": hotel_details[2]
            }
        else:
            flash("Invalid hotel details.", "warning")


    # Check if all necessary fields are present
    if not all([start_date, end_date, departure_city, arrival_city, flight_needed, car_needed, hotel_stars, budget]):
        flash("Missing fields for generating itinerary.", "warning")
        return redirect(url_for('itinerary'))
    
    user_prompt = f"""
        Generate a detailed travel itinerary in JSON format. Ensure the itinerary includes all necessary details, including timestamps, addresses, travel durations, and costs. Use the following JSON structure:

        {{
            "header": {{
                "departure_city": "",
                "arrival_city": "",
                "start_date": "",
                "end_date": "",
                "car_rental_info": {{
                    "company": "",
                    "car_type": "",
                    "pick_up_location": "",
                    "pick_up_time": "",
                    "return_location": "",
                    "return_time": "",
                    "total_price": ""
                }}
            }},
            "content": [
                {{
                    "place": "",
                    "location": "",
                    "time_stamp": "",
                    "description": "",
                    "price": ""
                }}
            ]
        }}

        Requirements:
        1. Travel Dates: From {start_date} to {end_date}. Ensure activities & all meals are generated for each day.
        2. Departure City: {departure_city}.
        3. Arrival City: {arrival_city}.
        4. Flight Details:
        - Required: {flight_needed}.
        - Departure Flight Price: {departing_flight}.
        - Return Flight Price: {returning_flight}.
        - Multiply the flight prices by total number of people.
        - If flight is not needed, assume they're driving to with a car rental starting from the departure city.
        5. Car Rental:
        - Required: {car_needed}.
        - If a car rental is required, include details under "car_rental_info". If not, set "car_rental_info" as an empty object.
        - Pickup & return should be from the departure city. Factor in driving time to reach the arrival city.
        6. Budget Level: {budget or "Not specified"}.
        7. Travelers: {num_adults} adults, {num_children} children.
        8. Accommodation:
        - Hotel: {hotel} (The given price is the rate per night. Include this rate at the end of each night).
        - Add the hotel stay to the end of each day but label it as overnight stay in the itinerary.
        - Do not add costs for check-in and check-out.
        9. Preferences:
        - Keywords: {keywords} (Use these to prioritize activities or destinations).
        - Include detailed descriptions for each activity or place to visit.
        - Provide timestamps and detailed costs for all activities and meals.
        10. Additional Considerations:
            - Account for travel time to/from the airport.
            - Ensure the itinerary starts and ends with flights only if "flight_needed" is true.
            - Include all meals every day.
            - Add necessary transportation for each activity.

        Formatting Rules:
        - Use clear timestamps (e.g., "2024-12-03T09:00").
        - For price, ONLY return numbers.
        - Avoid using the character \u2019 for apostrophes.
        - Use a dictionary for the "content" array.
        """

    # Generate response from OpenAI
    completion = openai.ChatCompletion.create(
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
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Departure City: {header['departure_city']}", ln=True)
    pdf.cell(0, 10, f"Arrival City: {header['arrival_city']}", ln=True)
    pdf.cell(0, 10, f"Number of Adults: {num_adults}", ln=True)
    pdf.cell(0, 10, f"Number of Children: {num_children}", ln=True)
    pdf.cell(0, 10, f"Travel Dates: From {header['start_date']} to {header['end_date']}", ln=True)
    pdf.ln(5)

    total_price = 0
    # Add Car Rental Info
    car_rental = header.get('car_rental_info', {})
    if car_rental:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "Car Rental Information:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"  Company: {car_rental.get('company', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Car Type: {car_rental.get('car_type', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Pickup Location: {car_rental.get('pick_up_location', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Pickup Time: {car_rental.get('pick_up_time', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Return Location: {car_rental.get('return_location', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Return Time: {car_rental.get('return_time', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"  Total Price: ${car_rental.get('total_price', 'N/A')}", ln=True)
        pdf.ln(10)
        price = int(car_rental.get('total_price', '0'))
        total_price += price

    content_list = pdf_content.get('content', [])

    if content_list:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "Schedule:", ln=True)
        curr_date = ""
        for content in content_list:
            if isinstance(content, dict):  # Check if content is a dictionary
                if content.get('price', '0') == "":
                    price = 0
                else: 
                    price = int(content.get('price', '0'))
                total_price += price
                # Parse the time
                date_obj = datetime.fromisoformat(content["time_stamp"])
                time_formatted = date_obj.strftime("%I:%M %p")  # e.g., 10:00 AM
                date_formatted = date_obj.strftime("%A %Y-%m-%d")  # e.g., Saturday 2024-12-14

                # Add the date header if the date changes
                if date_formatted != curr_date:
                    if curr_date is not None:
                        pdf.ln(5)  # Add spacing before a new date header
                    pdf.set_font("Arial", "B", 12)  # Bold font for the date header
                    pdf.cell(0, 10, date_formatted, border=1, ln=1, align="C")  # Full-width date header
                    curr_date = date_formatted

                # Add a row for the time and details
                pdf.set_font("Arial", size=12)  # Regular font for time and details

                # Define column widths
                time_column_width = 40  # Fixed width for the time column
                details_column_width = pdf.w - time_column_width - 20  # Remaining width for the details column (accounting for margins)

                # Time column
                pdf.cell(time_column_width, 10, time_formatted, border=0, ln=0, align='C')

                # Details column
                details = (
                    f"{content.get('place', 'N/A')}\n"
                    f"{content.get('location', 'N/A')}\n"
                    f"{content.get('description', 'N/A')}\n"
                    f"Price: ${content.get('price', 'N/A')}"
                )
                pdf.multi_cell(details_column_width, 10, details, border=1, align='L')

            elif isinstance(content, str):  # Handle string content
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, f"  Note: {content}")
                pdf.ln(5)
    else:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, "No destination information available.", ln=True)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"  Total Price: ${total_price}", ln=True, align='C')
    pdf.ln(10)

    # Determine if the PDF should be downloaded or displayed inline
    disposition = "inline" if request.args.get("action") == "view" else "attachment"

    # Create a response with the PDF
    response = make_response(pdf.output(dest='S').encode('latin1'))
    # response = make_response(pdf.output(dest='S').encode('utf-8'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'{disposition}; filename=itinerary.pdf'

    return response


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('sign_in'))

if __name__ == "__main__":
    app.run(debug=True)
