from datetime import datetime
import json
from pytz import timezone

# Remember to check pythonanywhere for updates to my files if i want to run the bot here
# https://www.pythonanywhere.com/user/steveisrich/files/home/steveisrich

# Greeting function for /start
def greet():
    sgt = timezone('Asia/Singapore')
    hr = datetime.now(sgt).hour
    greeting = None
    if 0 <= hr <= 5:
        greeting = "morning (You're either sleep deprived staying up so late or David Goggins waking up so early)"
    elif 6 <= hr <= 12:
        greeting = "morning"
    elif 13 <= hr <= 18:
        greeting = "afternoon"
    elif 19 <= hr <= 23:
        greeting = "evening"
    return greeting

# File for saving events
USER_EVENTS_FILE = 'user_events.json'
MATRIX_HIGHSCORE = 'matrix_highscore.json'
fun_facts = 'fun_facts.csv'

def fun_fact():
    """Loads fun_facts.csv.

    Returns:
        list: fun facts
    """
    facts = []
    with open(fun_facts, 'r', newline='') as file: # tbh can just use .txt file, don't need csv since i'm not separating anything by the commas
        for row in file:
            facts.append(row.strip())
    return facts

def load_user_events():
    """Loads user_events.json.
    Returns users' events as a dictionary
    """
    try:
        with open(USER_EVENTS_FILE, 'r') as file:
            data = json.load(file)
            if not data:
                return {}  # Return an empty dictionary if the file is empty
            return {int(key): value for key, value in data.items()} # Parses a valid JSON string """...""" and converts it into a python dictionary. key = chat_id, value = list of all events within that chat_id
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading user events: {e}") # If file is empty, this will show: Error loading user events: Expecting value: line 1 column 1 (char 0)
        return {} # Return an empty dictionary if there is an issue decoding JSON

# writing over the whole file, not appending
def save_user_events(user_events):
    """Saves users' events into user_events.json, chronologically sorting according to date.

    Args:
        user_events (dict): Dictionary with key = chat_id, values = list of dictionaries containing events and dates.
    """
    with open(USER_EVENTS_FILE, 'w') as file:
        for events in user_events.values(): # iterate through each id, be it chat_id or user_id
            events.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M'))
        json.dump(user_events, file)
        
def check_mounting(variable_date):
    """Checks mounting dates.

    Args:
        variable_date (date): datetime object.

    Returns:
        str: who is mounting.
    """
    # work_cycle = [2, 1, 2, 2, 1, 1, 3, 1, 1]
    work_cycle = [
        '1/4 is starting their mount', 
        '1/4 is mounting', 
        '2/3 is starting their mount', 
        '2/3 is mounting', 
        '2/3 is mounting', 
        '1/4 is starting their mount', 
        '1/4 is mounting', 
        '2/3 is starting their mount', 
        '2/3 is mounting', 
        '1/4 is starting their mount', 
        '1/4 is mounting', 
        '1/4 is mounting', 
        '2/3 is starting their mount', 
        '2/3 is mounting']

    reference_date = '2024-01-03' # on this date, the first element in work_cycle applies i.e. Mounting
    reference_formatted = datetime.strptime(reference_date, '%Y-%m-%d')

    total_days = len(work_cycle) #14
    delta_days = (variable_date - reference_formatted).days

    x = delta_days % total_days
    return work_cycle[x]

# retrieving high score for each unique chat_id from matrix_highscore.json
def load_highscore():
    """Loads highscore from matrix_highscore.json

    Returns:
        dict: key = chat_id, value = highscore int
    """
    try:
        with open(MATRIX_HIGHSCORE, 'r') as file:
            data = json.load(file)
            if not data:
                return {}
            return {int(key): value for key, value in data.items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading user events: {e}")
        return {}
    
def save_highscore(new_highscore):
    with open(MATRIX_HIGHSCORE, 'w') as file:
        json.dump(new_highscore, file)
    
""" debugging  
if __name__ == "__main__":
    fun_fact()
"""