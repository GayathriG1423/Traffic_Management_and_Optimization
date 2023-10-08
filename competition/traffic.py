from flask import Flask, render_template, request
import requests
import pandas as pd
import datetime
from urllib import parse as urlparse
import json

app = Flask(__name__)

# Replace with your Mapbox access token
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ2F5YXRocmkxIiwiYSI6ImNsYTE0OGdwaDAxenIzcG16bjc5OHg0MzAifQ.4Id6XVvt_DjBiOGm9lLv5Q'

def get_coordinates(location):
    geocoding_url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json?access_token={MAPBOX_ACCESS_TOKEN}'
    response = requests.get(geocoding_url)

    if response.status_code == 200:
        data = response.json()
        if data.get('features'):
            # Extract the first result
            result = data['features'][0]
            coordinates = result['center']
            return {'latitude': coordinates[1], 'longitude': coordinates[0]}
    
    # If no coordinates were found, return None
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_location = request.form.get('start_location')
        end_location = request.form.get('end_location')
        print(start_location)
        
        # Get coordinates for start and end locations
        start_coordinates = get_coordinates(start_location)
        end_coordinates = get_coordinates(end_location)
        
        if start_coordinates and end_coordinates:
            # Print the coordinates
            print(f'Start Location Coordinates: {start_coordinates}')
            print(f'End Location Coordinates: {end_coordinates}')

            # Define your base URL, start and end locations, and API key
            base_url = "https://api.tomtom.com/routing/1/calculateRoute/"
            start = f"{start_coordinates['latitude']},{start_coordinates['longitude']}"  
            end = f"{end_coordinates['latitude']},{end_coordinates['longitude']}"  
            key = "A7KmpCoDrHyrPoxijDfK39ZnWAb5xYug"

            # Initialize an empty DataFrame to store the results
            df = pd.DataFrame()
            data_list = []

            today = datetime.date.today()
            departure_time_start = datetime.datetime(today.year, today.month, today.day - 1, 0, 0, 0)

            hour_range = range(0, 24)

            # Inside the loop for hour_range
            for i in hour_range:
                # Update an hour
                departure_time = departure_time_start.replace(hour=departure_time_start.hour + i)

                # Format datetime string
                departure_time = departure_time.strftime('%Y-%m-%dT%H:%M:%S')

                # Create request URL
                request_params = (
                    urlparse.quote(start) + ":" + urlparse.quote(end)
                    + "/json?departAt=" + urlparse.quote(departure_time))

                request_url = base_url + request_params + "&key=" + key

                # Get data
                response = requests.get(request_url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Convert to JSON
                    json_result = response.json()

                    # Get the first route
                    route = json_result['routes'][0]

                    # Extract latitude and longitude of start and end points
                    start_point = route['legs'][0]['points'][0]  # First point of the first leg
                    end_point = route['legs'][0]['points'][-1]   # Last point of the first leg

                    data_dict = {
                        'index': i,
                        'lengthInMeters': route['summary']['lengthInMeters'],
                        'travelTimeInSeconds': route['summary']['travelTimeInSeconds'],
                        'trafficDelayInSeconds': route['summary']['trafficDelayInSeconds'],
                        'trafficLengthInMeters': route['summary']['trafficLengthInMeters'],
                        'departureTime': departure_time,
                        'arrivalTime': route['summary']['arrivalTime'],
                        'Start Latitude': start_point['latitude'],
                        'Start Longitude': start_point['longitude'],
                        'End Latitude': end_point['latitude'],
                        'End Longitude': end_point['longitude']
                    }

                    # Append the dictionary as a new row to the DataFrame
                    data_list.append(data_dict)

                    # print(f"Retrieving data: {i + 1} / {len(hour_range)}")
                    # print(f"Start Point: Latitude {start_point['latitude']}, Longitude {start_point['longitude']}")
                    # print(f"End Point: Latitude {end_point['latitude']}, Longitude {end_point['longitude']}")
            df = pd.DataFrame(data_list)
            print(df)
            json_data = df.to_json(orient='records')
            print(json_data)
            routes = json.loads(json_data)

            # Function to calculate distance between two points (e.g., routes)
            def calculate_distance(route1, route2):
                # You can use any distance metric here. For simplicity, we use the lengthInMeters.
                return route1["lengthInMeters"]

            # Function to find the top 3 routes with the shortest time and distance
            def find_top_1_routes(routes):
                reference_route = routes[0]  # Choose a reference route
                routes.sort(key=lambda x: (x["travelTimeInSeconds"], calculate_distance(x, reference_route)))
                return routes[:1]

            # Print the top 3 routes
            top_1_routes = find_top_1_routes(routes)
            for route in top_1_routes:
                print(f"Departure: {route['departureTime']} - Arrival: {route['arrivalTime']}")
                print(f"Travel Time (seconds): {route['travelTimeInSeconds']}")
                print(f"Distance (meters): {route['lengthInMeters']}")
                print(f"Start Latitude: {route['Start Latitude']}")
                print(f"Start Longitude: {route['Start Longitude']}")
                print(f"End Latitude: {route['End Latitude']}")
                print(f"End Longitude: {route['End Longitude']}")
            
            print(start_coordinates)
            
            return render_template('traffic.html', distance=route['lengthInMeters'], start_coords=start_coordinates, end_coords=end_coordinates)


        else:
            return 'Location not found or coordinates not available.'

    return render_template('traffic.html')

if __name__ == '__main__':
    app.run(debug=False)  # Disable debug mode
