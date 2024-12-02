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
from datetime import datetime

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
#SERPAPI Key
serpAPI_key=os.getenv("OPENSERP_API_KEY")
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
        return redirect(url_for('outboundFlight', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                flight_needed=flight_needed, car_needed=car_needed,
                                hotel_stars=hotel_stars, budget=budget))
    

    return render_template('confirmation.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                           flight_needed=flight_needed, hotel_stars=hotel_stars,
                           car_needed=car_needed)

                           


@app.route('/outboundFlight')
@login_required
def flight_car_API_call():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')
    hotel_stars = request.args.get('hotel_stars')
    flight_needed = request.args.get('flight_needed')
    car_needed=request.args.get('car_needed')
 
    OutBoundParams= { 
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
        "adults":1,#need to update with adults num variable
        "children":0, #need to update with child num variable
        "max_price":budget,
        "api_key": "serpAPI_key"

        }

    OutBoundSearch= GoogleSearch(OutBoundParams)
    results = OutBoundSearch.get_dict()

    OutBound_flight_list=[]

    OutBound_results= results
    search_info=OutBound_results['search_metadata']
    status=search_info['status']
    if status=='Success':
        if 'best_flights' in OutBound_results.keys():
            first_flight=OutBound_results["best_flights"][0]
            second_flight=OutBound_results["best_flights"][1]
            third_flight=OutBound_results["best_flights"][2]
            OutBound_flight_list.append(first_flight)
            OutBound_flight_list.append(second_flight)
            OutBound_flight_list.append(third_flight)

            OutBound_flight1=[]
            OutBound_flight2=[]
            OutBound_flight3=[]

            counter=1
            for items in OutBound_flight_list:
                if counter==4:
                    break
                else:
                    for one in items['flights']:
                        if counter==1:
                            OutBound_flight1.append(one['flight_number'])
                            OutBound_flight1.append(items['price'])
                            OutBound_flight1.append(one['departure_airport']['name'])
                            OutBound_flight1.append(one['departure_airport']['time'].split()[0])
                            OutBound_flight1.append(one['departure_airport']['time'].split()[1])
                            OutBound_flight1.append(one['arrival_airport']['name'])
                            OutBound_flight1.append(one['arrival_airport']['time'].split()[0])
                            OutBound_flight1.append(one['arrival_airport']['time'].split()[1])
                            OutBound_flight1.append(items['departure_token'])  

                        elif counter==2:
                            OutBound_flight2.append(one['flight_number'])
                            OutBound_flight2.append(items['price'])
                            OutBound_flight2.append(one['departure_airport']['name'])
                            OutBound_flight2.append(one['departure_airport']['time'].split()[0])
                            OutBound_flight2.append(one['departure_airport']['time'].split()[1])
                            OutBound_flight2.append(one['arrival_airport']['name'])
                            OutBound_flight2.append(one['arrival_airport']['time'].split()[0])
                            OutBound_flight2.append(one['arrival_airport']['time'].split()[1])
                            OutBound_flight2.append(items['departure_token'])
                    
                        else:
                            OutBound_flight3.append(one['flight_number'])
                            OutBound_flight3.append(items['price'])
                            OutBound_flight3.append(one['departure_airport']['name'])
                            OutBound_flight3.append(one['departure_airport']['time'].split()[0])
                            OutBound_flight3.append(one['departure_airport']['time'].split()[1])
                            OutBound_flight3.append(one['arrival_airport']['name'])
                            OutBound_flight3.append(one['arrival_airport']['time'].split()[0])
                            OutBound_flight3.append(one['arrival_airport']['time'].split()[1])
                            OutBound_flight3.append(items['departure_token'])

                        counter+=1

            Outbound_flight1_code, Outbound_flight1_cost, Outbound_flight1_departure_airport, Outbound_flight1_startDate, Outbound_flight1_startTime, Outbound_flight1_arrival_airport, Outbound_flight1_endDate, Outbound_flight1_endTime, Outbound_flight1_dep_token =OutBound_flight1
            Outbound_flight2_code, Outbound_flight2_cost, Outbound_flight2_departure_airport, Outbound_flight2_startDate, Outbound_flight2_startTime, Outbound_flight2_arrival_airport, Outbound_flight2_endDate, Outbound_flight2_endTime, Outbound_flight2_dep_token =OutBound_flight2
            Outbound_flight3_code, Outbound_flight3_cost, Outbound_flight3_departure_airport, Outbound_flight3_startDate, Outbound_flight3_startTime, Outbound_flight3_arrival_airport, Outbound_flight3_endDate, Outbound_flight3_endTime, Outbound_flight3_dep_token =OutBound_flight3
            #creating strings for OpenAI
            OutboundFlight1_details=','.join(map(str,OutBound_flight1))
            OutboundFlight2_details=','.join(map(str,OutBound_flight2))
            OutboundFlight3_details=','.join(map(str,OutBound_flight3))

        if request.method=="POST":
            return redirect(url_for('flightarrival', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                keywords=keywords,flight_needed=flight_needed, car_needed=car_needed,hotel_stars=hotel_stars, budget=budget,Outbound_flight1_dep_token=Outbound_flight1_dep_token or None,
                                Outbound_flight2_dep_token=Outbound_flight2_dep_token or None,Outbound_flight3_dep_token=Outbound_flight3_dep_token or None, status=status or None,
                                OutboundFlight1_details=OutboundFlight1_details or None,OutboundFlight2_details=OutboundFlight2_details or None,
                                OutboundFlight3_details=OutboundFlight3_details or None))
        
        
        else:
            #if no results were found given parameters
            print("No flights were found for in the search given selected options. Please try again.")
            return False
    else:
        #if error with api
        print(f"success status: {status}")
        
    return render_template('outboundFlight.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city
                           ,Outbound_flight1_code=Outbound_flight1_code or None,Outbound_flight1_cost=Outbound_flight1_cost or None,
                           Outbound_flight1_departure_airport=Outbound_flight1_departure_airport or None,Outbound_flight1_startDate=Outbound_flight1_startDate or None,
                           Outbound_flight1_startTime=Outbound_flight1_startTime or None,Outbound_flight1_arrival_airport=Outbound_flight1_arrival_airport or None,
                           Outbound_flight1_endDate=Outbound_flight1_endDate or None,Outbound_flight1_endTime=Outbound_flight1_endTime or None,Outbound_flight1_dep_token=Outbound_flight1_dep_token or None,
                            Outbound_flight2_code=Outbound_flight2_code or None,Outbound_flight2_cost=Outbound_flight2_cost or None,
                           Outbound_flight2_departure_airport=Outbound_flight2_departure_airport or None,Outbound_flight2_startDate=Outbound_flight2_startDate or None,
                           Outbound_flight2_startTime=Outbound_flight2_startTime or None,Outbound_flight2_arrival_airport=Outbound_flight2_arrival_airport or None,
                           Outbound_flight2_endDate=Outbound_flight2_endDate or None,Outbound_flight2_endTime=Outbound_flight2_endTime or None,Outbound_flight2_dep_token=Outbound_flight2_dep_token or None,
                           Outbound_flight3_code=Outbound_flight3_code or None,Outbound_flight3_cost=Outbound_flight3_cost or None,
                           Outbound_flight3_departure_airport=Outbound_flight3_departure_airport or None,Outbound_flight3_startDate=Outbound_flight3_startDate or None,
                           Outbound_flight3_startTime=Outbound_flight3_startTime or None,Outbound_flight3_arrival_airport=Outbound_flight3_arrival_airport or None,
                           Outbound_flight3_endDate=Outbound_flight3_endDate or None,Outbound_flight3_endTime=Outbound_flight3_endTime or None,Outbound_flight3_dep_token=Outbound_flight3_dep_token or None
                           )
@app.route('/returnFlight')
@login_required
def deaprtureflight():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    flight_needed = request.args.get('flight_needed')
    car_needed=request.args.get('car_needed')
    budget = request.args.get('budget')
    keywords = request.args.get('keywords')
    hotel_stars = request.args.get('hotel_stars')
    status = request.args.get('status')
    Outbound_flight1_dep_token=request.args.get('Outbound_flight1_dep_token')
    Outbound_flight2_dep_token=request.args.get('Outbound_flight2_dep_token')
    Outbound_flight3_dep_token=request.args.get('Outbound_flight3_dep_token')
    #arrival flight API call
    returnParams= { 
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
    def returnFlight(returnparams,dep_token,departureList):
            returnparams['departure_token']=dep_token
            returnSearch= GoogleSearch(returnparams)
            return_results = returnSearch.get_dict()
            if 'other_flights' in return_results.keys():
                first_return_flight=return_results['other_flights'][0]
                for infomation in first_return_flight['flights']:
                    departureList.append(infomation['flight_number'])
                    departureList.append(first_return_flight['price'])
                    departureList.append(infomation['departure_airport']['name'])
                    departureList.append(infomation['departure_airport']['time'].split()[0])
                    departureList.append(infomation['departure_airport']['time'].split()[1])
                    departureList.append(infomation['arrival_airport']['name'])
                    departureList.append(infomation['arrival_airport']['time'].split()[0])
                    departureList.append(infomation['arrival_airport']['time'].split()[1])
                return (departureList)
            else:
                return (departureList)

    returnFlight1=[]
    returnFlight2=[]
    returnFlight3=[]
    if status=='Success':

        returnFlight(returnParams, Outbound_flight1_dep_token,returnFlight1)
        returnFlight(returnParams, Outbound_flight2_dep_token,returnFlight2)
        returnFlight(returnParams, Outbound_flight3_dep_token,returnFlight3)

        if returnFlight1 & returnFlight2 & returnFlight3:
            returnFlight1_code, returnFlight1_cost, returnFlight1_departure_airport, returnFlight1_startDate, returnFlight1_startTime, returnFlight1_arrival_airport, returnFlight1_endDate, returnFlight1_endTime =returnFlight1
            returnFlight2_code, returnFlight2_cost, returnFlight2_departure_airport, returnFlight2_startDate, returnFlight2_startTime, returnFlight2_arrival_airport, returnFlight2_endDate, returnFlight2_endTime =returnFlight2
            returnFlight3_code, returnFlight3_cost, returnFlight3_departure_airport, returnFlight3_startDate, returnFlight3_startTime, returnFlight3_arrival_airport, returnFlight3_endDate, returnFlight3_endTime =returnFlight3
    
            #Creating OpenAI string w/ return flight details
            ReturnFlight1_details=','.join(map(str,returnFlight1))
            ReturnFlight2_details=','.join(map(str,returnFlight2))
            ReturnFlight3_details=','.join(map(str,returnFlight3))

        else:
            message="No flights found with chosen prefernces"
            return message
    
    else:
        print("Error with API")
        print(f"success status: {status}")

    if request.method=="POST":
            return redirect(url_for('hotel', start_date=start_date, end_date=end_date,
                                departure_city=departure_city, arrival_city=arrival_city,
                                flight_needed=flight_needed, car_needed=car_needed,hotel_stars=hotel_stars, budget=budget,
                                ReturnFlight1_details=ReturnFlight1_details or None,ReturnFlight2_details=ReturnFlight2_details or None,ReturnFlight3_details=ReturnFlight3_details or None))
    
    return render_template('returnFlight.html', start_date=start_date, end_date=end_date,
                           departure_city=departure_city, arrival_city=arrival_city,
                            hotel_stars=hotel_stars,returnFlight1_code=returnFlight1_code,returnFlight1_cost=returnFlight1_cost,
                            returnFlight1_departure_airport=returnFlight1_departure_airport or None,returnFlight1_startDate=returnFlight1_startDate or None,
                            returnFlight1_startTime=returnFlight1_startTime or None,returnFlight1_arrival_airport=returnFlight1_arrival_airport or None,
                           returnFlight1_endDate=returnFlight1_endDate or None,returnFlight1_endTime=returnFlight1_endTime or None,
                           
                           returnFlight2_code=returnFlight2_code or None,returnFlight2_cost=returnFlight2_cost or None,
                            returnFlight2_departure_airport=returnFlight2_departure_airport or None,returnFlight2_startDate=returnFlight2_startDate or None,
                            returnFlight2_startTime=returnFlight2_startTime or None,returnFlight2_arrival_airport=returnFlight2_arrival_airport or None,
                           returnFlight2_endDate=returnFlight2_endDate or None,returnFlight2_endTime=returnFlight2_endTime or None,

                           returnFlight3_code=returnFlight3_code or None,returnFlight3_cost=returnFlight3_cost or None,
                            returnFlight3_departure_airport=returnFlight3_departure_airport or None,returnFlight3_startDate=returnFlight3_startDate or None,
                            returnFlight3_startTime=returnFlight3_startTime or None,returnFlight3_arrival_airport=returnFlight3_arrival_airport or None,
                           returnFlight3_endDate=returnFlight3_endDate or None,returnFlight3_endTime=returnFlight3_endTime or None,
                           )

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
    keywords = request.args.get('keywords')
    num_adults = request.args.get('adults', 0) 
    num_children = request.args.get('children', 0) 
    departing_flight = request.args.get('departing_flight') 
    returning_flight = request.args.get('returning_flight') 
    hotel = request.args.get('hotel')

    if not all([start_date, end_date, departure_city, arrival_city, flight_needed, car_needed, hotel_stars, budget, keywords, num_adults, num_children, departing_flight, returning_flight, hotel]):
        # Create an instance of FPDF
        pdf = FPDF()
        pdf.add_page()  # Add a blank page

        # Optional: Add minimal content, like a title or message
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Missing fields to generate itinerary", ln=True, align="C")

        if not start_date:
            pdf.cell(0, 10, "No start date provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Start Date: {start_date}", ln=True, align="C")

        if not end_date:
            pdf.cell(0, 10, "No end date provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"End Date: {end_date}", ln=True, align="C")

        if not departure_city:
            pdf.cell(0, 10, "No departure city provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Departure City: {departure_city}", ln=True, align="C")

        if not arrival_city:
            pdf.cell(0, 10, "No arrival city provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Arrival City: {arrival_city}", ln=True, align="C")

        if not flight_needed:
            pdf.cell(0, 10, "Flight needed status not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Flight Needed: {flight_needed}", ln=True, align="C")

        if not car_needed:
            pdf.cell(0, 10, "Car needed status not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Car Needed: {car_needed}", ln=True, align="C")

        if not hotel_stars:
            pdf.cell(0, 10, "Hotel stars not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Hotel Stars: {hotel_stars}", ln=True, align="C")

        if not budget:
            pdf.cell(0, 10, "Budget not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Budget: {budget}", ln=True, align="C")

        if not keywords:
            pdf.cell(0, 10, "No keywords provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Keywords: {keywords}", ln=True, align="C")

        if not num_adults:
            pdf.cell(0, 10, "Number of adults not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Number of Adults: {num_adults}", ln=True, align="C")

        if not num_children:
            pdf.cell(0, 10, "Number of children not provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Number of Children: {num_children}", ln=True, align="C")

        if not departing_flight:
            pdf.cell(0, 10, "No departing flight information", ln=True, align="C")
        else:
            pdf.multi_cell(0, 10, f"Departing Flight: {departing_flight}", align="L")

        if not returning_flight:
            pdf.cell(0, 10, "No returning flight information", ln=True, align="C")
        else:
            pdf.multi_cell(0, 10, f"Returning Flight: {returning_flight}", align="L")

        if not hotel:
            pdf.cell(0, 10, "No hotel information provided", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Hotel: {hotel}", ln=True, align="C")

        # Output PDF as a binary response
        response = make_response(pdf.output(dest='S').encode('latin1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=blank_document.pdf'
        return response

    user_prompt = f"""Generate a detailed travel itinerary in JSON format. Ensure the itinerary includes all necessary details such as timestamps, addresses, travel durations, and costs. Use the following headers for the JSON structure:
    json headers: \"header\": \"departure_city\", \"arrival_city\", \"start_date\", \"end_date\", \"car_rental_info\": \"company\", \"car_type\", \"pick_up_location\", \"pick_up_time\", \"return_location\", \"return_time\", \"total_price\", 
    \"content\": \"place\", \"location\", \"time_stamp\", \"description\", \"price\"\n
    Requirements: 
    1. Travel Dates: From {start_date} to {end_date}
    2. Departure City: {departure_city}
    3. Arrival City: {arrival_city}
    4. Flight Required: {flight_needed} {departing_flight} {returning_flight}
    6. Car Rental Required: {car_needed} - If renting a car, include rental details at the start of the itinerary under \"car_rental_info\". If not, leave \"car_rental_info\" as an empty object. 
    7. Budget Level: {budget or "Not specified"} 
    8. {num_adults} Adults, {num_children} Children
    9. Hotel: {hotel}
    10. Keywords: {keywords}
    11. Additional Details: - Factor in travel time to/from the airport. 
    - Include descriptions of activities or places to visit in destination.
    - Provide a timestamp and detailed cost for each activity.
    - Plan activities based on keywords for preferences
    - Include transportation if necessary
    - Include all meals every day
    - All numbers for prices"""

    # simple user prompt to test with
    # user_prompt = f'''return json object where json headers: \"header\": \"departure city\", \"arrival city\", \"start_date\", \"end_date\", \"car rental info\",: \"content\": \"place\", \"location\", \"time stamp\", \"description\", \"price\"\n, one for header and car rental, two content items 
    # always number as a string for price'''

    # test link: http://127.0.0.1:5000/generate-itinerary?start_date=2024-12-13&end_date=2024-12-15&departure_city=Boston&arrival_city=New+York&flight_needed=yes&car_needed=yes&hotel_stars=4&budget=mid&keywords=child-friendly,food,tourist+attractions&adults=2&children=2&departing_flight=B6+217,$574,Boston+Logan+International+Airport,2024-12-14,05:39,John+F.+Kennedy+International+Airport,2024-12-14,07:00&returning_flight=B6+1318,2024-12-15,13:15,John+F.+Kennedy+International+Airport,2024-12-15,14:35,Boston+Logan+International+Airport&hotel=Hyatt+Grand+Central+New+York+-+Price:$361&action=view


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
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Departure City: {header['departure_city']}", ln=True)
    pdf.cell(0, 10, f"Arrival City: {header['arrival_city']}", ln=True)
    pdf.cell(0, 10, f"Travel Dates: From {header['start_date']} to {header['end_date']}", ln=True)
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
        curr_date = ""
        for content in content_list:
            if isinstance(content, dict):  # Check if content is a dictionary
                price = content.get('price', '0')
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

if __name__ == "__main__":
    app.run(debug=True)
