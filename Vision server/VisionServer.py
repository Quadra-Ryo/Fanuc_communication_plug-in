import socket
import random
import time

from typing import Tuple # Import done to maintain retroactivity for Python versions prior to 3.9

HOST = '0.0.0.0'  # All interfaces
PORT = 1313       # Opened TCP Port

# This function simulates a Vision System response
def get_response(msg:str) -> Tuple[str, int]:
    state = 0
    
    match msg:
        case "locate": # Locate an object in the vision area
            # Randomizing the data to return
            n = random.randint(1,4)
            x = round(random.uniform(1,100),2)
            y = round(random.uniform(1,100),2)
            rz = round(random.uniform(1,100),2)
            
            # Formatting the response with the type of object detected and the coordinates 
            response = f"Object_{n};{x};{y};{rz}"
        
        case "state": # Current state of the camera
            # Randomizing a simple state of the camera
            n = random.randint(1,50)
            if n == 1:
                response = "# Error: Camera is not working"
            else:
                response = "ACK_Camera working"
                
        case "end_vision": # End the vision
            response = "Vision ended"
            state = -1
            
        case "start_vision": # Starts the vision    
            response = "Vision started"
            state = +1
            
        case _: # Default case, handled like a custom command
            response = f"Executing ({msg})"
            
    return (response, state) 
         
# Simulating the actual vision server             
def start_server():
    vision_system_state = -1 # Setting the state of the vision system to "off"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Socket set-up
            s.bind((HOST, PORT))
            s.listen()
            print(f"DEBUG: Listening on [{HOST} : {PORT}]")
            conn, addr = s.accept()
        
            with conn:
                print(f"DEBUG: Connection accepted {addr}")
                
                while True:
                    data = conn.recv(1024) # Waiting for a string from the robot 
                    if  not data:
                        msg_to_send = "# Error: no data received"
                    else:    
                        msg = data.decode()
                        msg_l = msg.lower().strip() # Making the server not case_sensitive to avoid errors
                        print(f"DEBUG: Received data: {msg}")
                        
                        if vision_system_state < 0 and msg_l != "start_vision":
                            msg_to_send = "#Error: The vision system is off"
                        else:
                            command = get_response(msg_l)                    
                            msg_to_send = command[0]
                            vision_system_state = command[1]
                            
                    conn.sendall(msg_to_send.encode())
                    print(f"DEBUG: Sent \"{msg_to_send}\"")
                    print(f"DEBUG: Vision state: {vision_system_state}")
        # Error handling
        except socket.error as e:
            print(f"ERROR: Socket error occurred: {e}")
            return -1
        except Exception as e:
            print(f"ERROR: An unexpected error occurred: {e}")
            return -1
               
if __name__ == "__main__":
    restart_flag = -1
    
    while restart_flag == -1: 
        # This loop restarts the server if a disconnection occurs
        restart_flag = start_server()
        print("DEBUG: Restarting the server")
        time.sleep(3) # Sleeping for 3 seconds before restart
