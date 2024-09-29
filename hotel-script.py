import json
with open('hotel-sample.json', 'r') as file:
    data = json.load(file)

hotel_names = [property['name'] for property in data['properties'] if property['type'] == 'hotel']

print(hotel_names)