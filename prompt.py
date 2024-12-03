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
1. Travel Dates: From {start_date} to {end_date}.
2. Departure City: {departure_city}.
3. Arrival City: {arrival_city}.
4. Flight Details:
   - Required: {flight_needed}.
   - Departure Flight Price: {departing_flight}.
   - Return Flight Price: {returning_flight}.
5. Car Rental:
   - Required: {car_needed}.
   - If a car rental is required, include details under "car_rental_info". If not, set "car_rental_info" as an empty object.
6. Budget Level: {budget or "Not specified"}.
7. Travelers: {num_adults} adults, {num_children} children.
8. Accommodation:
   - Hotel: {hotel} (Include nightly rate in the total cost).
   - Add the hotel stay to the end of each day in the itinerary.
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
- Include all numbers for prices.
- Avoid using the character \u2019 for apostrophes.
- Use a dictionary for the "content" array.
"""
