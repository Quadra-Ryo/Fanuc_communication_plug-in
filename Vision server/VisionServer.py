import socket
import random
import time

from typing import Tuple # Import done to maintain retroactivity for Python versions prior to 3.9

HOST = '0.0.0.0'  # All interfaces
PORT = 1313       # Opened TCP Port
DEBUG_MODE = True # Debug on

def debug(msg): # Debug function to enable to turn off the debug mode
    if DEBUG_MODE:
        print(f"DEBUG: {msg}")

def locate(): # Randomizing the values of an object to simulate a vision system
    vision_state = state()
    if vision_state[1] > 0:
        n = random.randint(1, 4)
        x = round(random.uniform(1, 100), 2)
        y = round(random.uniform(1, 100), 2)
        rz = round(random.uniform(1, 100), 2)
        return (f"Object_{n};{x};{y};{rz}", 1)
    else:
         return ("# Error: Camera runned into an error!", -2)
     
def state(): # Randomizing the state of the camera
    n = random.randint(1, 100)
    if n == 1:
        return ("# Error: Camera is not working", -2)
    else:
        return ("ACK_Camera working", 1)

def start_vision(): # Command to start the vision system
    return ("Vision started", 1)

def end_vision(): # Command to turn off the vision system
    return ("Vision ended", -1)

def default(msg): # Default commands
    return (f"Executing ({msg})", 1)

# Dispatcher dictionary to avoid using the match-case (Compatibility with versions < 3.10)
DISPATCHER = {
    "locate": locate,
    "state": state,
    "start_vision": start_vision,
    "end_vision": end_vision
} # Handles the different commands 

# This function simulates a Vision System response
def get_response(msg:str) -> Tuple[str, int]:
    return DISPATCHER.get(msg, lambda: default(msg))() # Executing the command if it's in the dispatcher otherwise executing the default command
         
# Simulating the actual vision server             
def start_server():
    vision_system_state = -1 # Setting the state of the vision system to "off"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Socket set-up
            s.bind((HOST, PORT))
            s.listen()
            debug(f"DEBUG: Listening on [{HOST} : {PORT}]")
            conn, addr = s.accept()
        
            with conn:
                debug(f"DEBUG: Connection accepted {addr}")
                
                while True:
                    data = conn.recv(1024) # Waiting for a string from the robot
                    
                    if  not data:
                        msg_to_send = "# Error: no data received"
                    else:    
                        msg = data.decode()
                        normalized_msg = msg.lower().strip() # Making the server not case_sensitive to avoid errors
                        debug(f"DEBUG: Received data: {msg}")
                        
                        if vision_system_state == -1 and normalized_msg != "start_vision":
                            msg_to_send = "#Error: The vision system is off"   
                        elif vision_system_state == -2 and normalized_msg != "end_vision":
                            msg_to_send = "#Error: The vision system runned into an error, please turn off the camera and than back on"
                        else:
                            command = get_response(normalized_msg)                    
                            msg_to_send = command[0]
                            vision_system_state = command[1]
                            
                    conn.sendall(msg_to_send.encode())
                    debug(f"DEBUG: Sent \"{msg_to_send}\"")
                    debug(f"DEBUG: Vision state: {vision_system_state}")
        # Error handling
        except socket.error as e:
            debug(f"ERROR: Socket error occurred: {e}")
            return -1
        except Exception as e:
            debug(f"ERROR: An unexpected error occurred: {e}")
            return -1
               
if __name__ == "__main__":
    restart_flag = -1
    
    while restart_flag == -1: 
        # This loop restarts the server if a disconnection occurs
        restart_flag = start_server()
        debug("DEBUG: Restarting the server")
        time.sleep(3) # Sleeping for 3 seconds before restart
