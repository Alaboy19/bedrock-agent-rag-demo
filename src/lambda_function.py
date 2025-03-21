import random
import datetime
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Dummy Weather API Endpoint (Replace with actual API)
WEATHER_API_URL = "https://api.example.com/weather"

def unpack_parameters(parameters):
    result = {}
    for param in parameters:
        name = param.get("name")
        value = param.get("value")
        
        if name is not None:
            if value is not None:
                # Try to convert to int or float if possible
                try:
                    result[name] = int(value)
                except ValueError:
                    try:
                        result[name] = float(value)
                    except ValueError:
                        result[name] = value  # Keep as string if not a number
            else:
                result[name] = None  # Handle missing value
    
    return result

def lambda_handler(event, context):

    logger.info("Received event: %s", json.dumps(event))  # Logs the incoming request
    
    #agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    responseBody =  {
        "TEXT": {
            "body": ""
        }
    } 

    """Handles actions based on user input."""
    
    function_name = event.get("function")
    logger.info(f"function_name: {function_name}")  # Logs the response

    parameters = event.get('parameters', [])
    unpacked_parameters = unpack_parameters(parameters)

    logger.info(f"unpacked parameters: {unpack_parameters}")
    
    if function_name == "ask_support_team":
        responseBody['TEXT']['body'] = handle_support_request(unpacked_parameters)
    
    elif function_name == "weather_lookup":
        responseBody['TEXT']['body'] = handle_weather_lookup(unpacked_parameters)

    #logger.info("responseBody: %s", json.dumps(responseBody))  # Logs the response
    action_response = {
    "actionGroup": actionGroup,
    "function": function,
    "functionResponse": {
        "responseBody": responseBody
        }

    }

    dummy_function_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    logger.info("dummy_function_response: %s", json.dumps(dummy_function_response)) 

    return dummy_function_response
  
    
def handle_support_request(unpacked_parameters):
    """Handles support ticket creation."""
    user_email = unpacked_parameters.get("user_email", None)
    query = unpacked_parameters.get("query", None)

    # Generate a unique ticket ID
    ticket_id = f"SUP-{random.randint(1000, 9999)}-{int(datetime.datetime.now().timestamp())}"

    # Simulate sending to support team
    if any(value is not None and value != "" for value in (user_email, query)):
        response_message = f"Your query has been sent to the support team with Ticket ID: {ticket_id}. Support will reach out to you very soon at {user_email}."
    else:
        response_message = "Detail is missing"
    return response_message

def handle_weather_lookup(unpacked_parameters):
    """Handles weather lookup."""
    location = unpacked_parameters.get("location", None)#event["parameters"].get("location")
    date_str = unpacked_parameters.get("date", None)#event["parameters"].get("date")

    # Convert user-provided date to actual date format
    target_date = parse_date(date_str)

    # Call weather API
    weather_data = get_weather(location, target_date)

    # Improved travel advice logic
    travel_advice = generate_travel_advice(weather_data)
    if any(value is not None and value != "" for value in (location, date_str)):
        return f"weather_description: {weather_data}, travel_advice: {travel_advice}"
    else:
        return "Detail is missing"
      

def parse_date(date_str):
    """Parses the date from a user-provided input."""
    if "next" in date_str.lower():
        days_ahead = {"monday": 7, "tuesday": 8, "wednesday": 9,
                      "thursday": 10, "friday": 11, "saturday": 12, "sunday": 13}
        for day, offset in days_ahead.items():
            if day in date_str.lower():
                return (datetime.date.today() + datetime.timedelta(days=offset)).strftime("%Y-%m-%d")
    
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.date.today().strftime("%Y-%m-%d")  # Default to today if parsing fails

def get_weather(location, date):
    """Mocks weather information instead of making an API request."""
    weather_conditions = ["sunny", "rainy", "cloudy", "stormy", "snowy", "hot", "cold", "windy"]
    return random.choice(weather_conditions) 
    # """Fetches weather information from an API."""
    # params = {"location": location, "date": date}
    
    # try:
    #     response = requests.get(WEATHER_API_URL, params=params)
    #     data = response.json()
    #     return data.get("weather", "unknown")  # Return weather condition
    # except Exception as e:
    #     return "unknown"  # Default in case of error

def generate_travel_advice(weather):
    """Generates travel advice based on weather conditions."""
    if weather == "rainy":
        return "It may rain, consider carrying an umbrella or postponing travel."
    elif weather == "snowy":
        return "Expect snow, dress warmly and check road conditions."
    elif weather == "stormy":
        return "Stormy weather ahead, avoid traveling if possible."
    elif weather == "hot":
        return "High temperatures expected, stay hydrated."
    elif weather == "cold":
        return "Cold weather, wear warm clothing."
    else:
        return "It's a good day to travel!"

