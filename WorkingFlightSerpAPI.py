
import json
from serpapi import GoogleSearch

import os
from dotenv import load_dotenv
import openai
load_dotenv()

destination= "destination.json"
#preset parms
departure_city= 'BOS',
arrival_city= 'JFK'
start_date='2024-12-14'
end_date='2025-02-13'
budget= '0'
adults='2'
children='1'

serpAPI_key=os.getenv("OPENSERP_API_KEY")

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
        "adults":adults,
        "children":children,
        "api_key":serpAPI_key,
        #'max_price':500
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
        flight1_details=','.join(map(str,OutBound_flight1))
        print("\nstring print out: "+flight1_details)

        # OutBound Flight 1 details
        print("OutBound Flight 1 Details:\n")
        print(f"Flight Code: {Outbound_flight1_code}")
        print(f"Cost: {Outbound_flight1_cost}")
        print(f"Departure Airport: {Outbound_flight1_departure_airport}")
        print(f"Start Date: {Outbound_flight1_startDate}")
        print(f"Start Time: {Outbound_flight1_startTime}")
        print(f"Arrival Airport: {Outbound_flight1_arrival_airport}")
        print(f"End Date: {Outbound_flight1_endDate}")
        print(f"End Time: {Outbound_flight1_endTime}")
        print(f"Departure Token: {Outbound_flight1_dep_token}")
        print('-' * 50)

        # OutBound Flight 2 details
        print("\nOutBound Flight 2 Details:\n")
        print(f"Flight Code: {Outbound_flight2_code}")
        print(f"Cost: {Outbound_flight2_cost}")
        print(f"Departure Airport: {Outbound_flight2_departure_airport}")
        print(f"Start Date: {Outbound_flight2_startDate}")
        print(f"Start Time: {Outbound_flight2_startTime}")
        print(f"Arrival Airport: {Outbound_flight2_arrival_airport}")
        print(f"End Date: {Outbound_flight2_endDate}")
        print(f"End Time: {Outbound_flight2_endTime}")
        print(f"Departure Token: {Outbound_flight2_dep_token}")
        print('-' * 50)

        # Flight 3 details
        print("\nOutBound Flight 3 Details:\n")
        print(f"Flight Code: {Outbound_flight3_code}")
        print(f"Cost: {Outbound_flight3_cost}")
        print(f"Departure Airport: {Outbound_flight3_departure_airport}")
        print(f"Start Date: {Outbound_flight3_startDate}")
        print(f"Start Time: {Outbound_flight3_startTime}")
        print(f"Arrival Airport: {Outbound_flight3_arrival_airport}")
        print(f"End Date: {Outbound_flight3_endDate}")
        print(f"End Time: {Outbound_flight3_endTime}")
        print(f"Departure Token: {Outbound_flight3_dep_token}")
        print('-' * 50)


        #GET RETURN FLIGHT BACK ------------------------------------------------------
        Returnparams= { 
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
        "adults":adults,
        "children":children,
        "api_key":serpAPI_key,       
        }

        def returnFlight(Returnparams,dep_token,departureList):
            Returnparams['departure_token']=dep_token
            returnSearch= GoogleSearch(Returnparams)
            return_results = returnSearch.get_dict()
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

        returnFlight1=[]
        returnFlight2=[]
        returnFlight3=[]
        returnFlight(Returnparams, Outbound_flight1_dep_token,returnFlight1)
        returnFlight(Returnparams, Outbound_flight2_dep_token,returnFlight2)
        returnFlight(Returnparams, Outbound_flight3_dep_token,returnFlight3)

        returnFlight1_code, returnFlight1_cost, returnFlight1_departure_airport, returnFlight1_startDate, returnFlight1_startTime, returnFlight1_arrival_airport, returnFlight1_endDate, returnFlight1_endTime =returnFlight1
        returnFlight2_code, returnFlight2_cost, returnFlight2_departure_airport, returnFlight2_startDate, returnFlight2_startTime, returnFlight2_arrival_airport, returnFlight2_endDate, returnFlight2_endTime =returnFlight2
        returnFlight3_code, returnFlight3_cost, returnFlight3_departure_airport, returnFlight3_startDate, returnFlight3_startTime, returnFlight3_arrival_airport, returnFlight3_endDate, returnFlight3_endTime =returnFlight3

        # Print for Return Flight1
        print(f"Return Flight 1:")
        print(f"Code: {returnFlight1_code}")
        print(f"Cost: {returnFlight1_cost}")
        print(f"Departure Airport: {returnFlight1_departure_airport}")
        print(f"Start Date: {returnFlight1_startDate}")
        print(f"Start Time: {returnFlight1_startTime}")
        print(f"Arrival Airport: {returnFlight1_arrival_airport}")
        print(f"End Date: {returnFlight1_endDate}")
        print(f"End Time: {returnFlight1_endTime}")
        print("-" * 50)  # Separator line for clarity

        # Print for Return Flight2
        print(f"Return Flight 2:")
        print(f"Code: {returnFlight2_code}")
        print(f"Cost: {returnFlight2_cost}")
        print(f"Departure Airport: {returnFlight2_departure_airport}")
        print(f"Start Date: {returnFlight2_startDate}")
        print(f"Start Time: {returnFlight2_startTime}")
        print(f"Arrival Airport: {returnFlight2_arrival_airport}")
        print(f"End Date: {returnFlight2_endDate}")
        print(f"End Time: {returnFlight2_endTime}")
        print("-" * 50)

        # Print for Return Flight3
        print(f"Return Flight 3:")
        print(f"Code: {returnFlight3_code}")
        print(f"Cost: {returnFlight3_cost}")
        print(f"Departure Airport: {returnFlight3_departure_airport}")
        print(f"Start Date: {returnFlight3_startDate}")
        print(f"Start Time: {returnFlight3_startTime}")
        print(f"Arrival Airport: {returnFlight3_arrival_airport}")
        print(f"End Date: {returnFlight3_endDate}")
        print(f"End Time: {returnFlight3_endTime}")
        print("-" * 50)
    else:
        print("No flights were found for in the search given selected options. Please try again.")
        #return False
else:
    print(f"success status: {status}")
    #return False
