import socket
import random
import time
import os

from datetime import datetime
from typing import Tuple # Import done to maintain retroactivity for Python versions prior to 3.9

HOST = '0.0.0.0'  # All interfaces
PORT = 1313       # Opened TCP Port
DEBUG_MODE = True # Debug on

# File paths compatible with Linux and macOS
ERROR_PATH = os.path.join("Vision server", "Files", "Error_log.txt")
RECIPE_PATH = os.path.join("Vision server", "Files", "Recipe.txt")
os.makedirs(os.path.dirname(ERROR_PATH), exist_ok=True)
os.makedirs(os.path.dirname(RECIPE_PATH), exist_ok=True)

def debug(msg): # Debug function to enable to turn off the debug mode
    if DEBUG_MODE:
        print(f"DEBUG: {msg}")

def error_log(msg): # Error handling
    if DEBUG_MODE:
        print(f"ERROR: {msg}")
        
    # Logging in the log file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_PATH, "a") as file:
        file.write(f"{timestamp}: ERROR: {msg}\n")
    
def locate(): # Randomizing the values of an object to simulate a vision system
    vision_state = state()
    if vision_state[1] > 0:
        n = random.randint(1, 3)
        x = round(random.uniform(1, 100), 2)
        y = round(random.uniform(1, 100), 2)
        rz = round(random.uniform(1, 100), 2)
        message = (f"Object_{n};{x};{y};{rz};", 1)
        debug(message[0])
    else:
        message = ("#Error : Camera ran into an error!", -2)
        error_log("Camera ran into an error!")
        
    return message

def state(): # Randomizing the state of the camera
    n = random.randint(1, 50)
    if n == 1:
        message = ("#Error: Camera is not working", -2)
        error_log("Camera is not working")
    else:
        message = ("ACK_Camera working", 1)
        debug(message[0])
        
    return (message)
    
def start_vision(): # Command to start the vision system
    return ("ACK_Vision started", 1)

def end_vision(): # Command to turn off the vision system
    return ("ACK_Vision ended", -1)

def default(msg): # Default commands
    return (f"ACK_Executing ({msg})", 1)

def get_recipe():
    with open(RECIPE_PATH, "r") as file:
        recipe_name = file.read()
    return (recipe_name, 1)

def set_recipe(recipe_name: str) -> Tuple[str, int]:
    try:
        with open(RECIPE_PATH, "w") as file:
            file.write(f"{recipe_name}")
        debug(f"Recipe set to {recipe_name}")
        return(f"ACK_Recipe set", 1)
    except Exception as e:
        error_log(f"Failed to write the recipe {e}")
        return("#Error: Failed to set recipe", -2)
    
# Dispatcher dictionary to avoid using the match-case (Compatibility with versions < 3.10)
DISPATCHER = {
    "locate": locate,
    "state": state,
    "start_vision": start_vision,
    "end_vision": end_vision,
    "get_recipe": get_recipe
} # Handles the different commands 

# This function simulates a Vision System response
def get_response(msg:str) -> Tuple[str, int]:
    if msg.startswith("set_recipe"):
        try:
            _, recipe = msg.split("=", 1)
            if not recipe:
                return ("#Error: Recipe name is empty", -2)
            return set_recipe(recipe)
        except ValueError:
            error_log("Invalid format for set_recipe (use set_recipe=name)")
            return ("#Error: Invalid format for set_recipe (use set_recipe=name)", 1)
            
    return DISPATCHER.get(msg, lambda: default(msg))() # Executing the command if it's in the dispatcher otherwise executing the default command

       
# Simulating the actual vision server             
def start_server():
    vision_system_state = -1 # Setting the state of the vision system to "off"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Socket set-up
            s.bind((HOST, PORT))
            s.listen()
            debug(f"Listening on [{HOST} : {PORT}]")
            conn, addr = s.accept()
        
            with conn:
                debug(f" Connection accepted {addr}")
                
                while True:
                    data = conn.recv(1024) # Waiting for a string from the robot
                    
                    if  not data:
                        error_log("no data received")
                        response_msg = "#Error: no data received"
                    else:    
                        msg = data.decode()
                        normalized_msg = ''.join(msg.lower().split()) # Making the server not case_sensitive to avoid errors
                        debug(f"Received data: {msg}")
                        
                        if vision_system_state == -1 and normalized_msg != "start_vision":
                            error_log("The vision system is off")
                            response_msg = "#Error: The vision system is off"   
                        elif vision_system_state == -2 and normalized_msg != "end_vision":
                            error_log("The vision system ran into an error, Please turn the camera off and then back on")
                            response_msg = "#Error: The vision system ran into an error, Please turn the camera off and then back on"
                        else:
                            command = get_response(normalized_msg)                    
                            response_msg = command[0]
                            vision_system_state = command[1]
                            
                    conn.sendall(response_msg.encode())
                    debug(f"Sent \"{response_msg}\"")
                    debug(f"Vision state: {vision_system_state}")
        # Error handling
        except socket.error as e:
            error_log(f"Socket error occurred: {e}")
            return -1
        except Exception as e:
            error_log(f"An unexpected error occurred: {e}")
            return -1
        
                   
if __name__ == "__main__":
    restart_flag = -1
    
    while restart_flag == -1: 
        # This loop restarts the server if a disconnection occurs
        restart_flag = start_server()
        debug("DEBUG: Restarting the server")
        time.sleep(3) # Sleeping for 3 seconds before restart
