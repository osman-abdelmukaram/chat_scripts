import socket
import threading
import os

## Terminal colors
GREEN = "\033[92m"
YELLOW = "\033[93m" 
RED = "\033[91m" 
RESET_COLOR = "\033[0m" 

#local IP addr., port 7000
IP_AND_PORT = socket.socket(socket.AF_INET, socket.SOCK_STREAM), 7000
BUFFER_SIZE = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

connected = False

recieve_send_ratio = 0

buffer_incoming = ""
new_data_in_buffer = False

recv_ids = {"x":3}
send_ids = {}


def get_valid_username():
    user_input = input("Please enter your username: ")

    if len(user_input) != 0:
        username = f"HELLO-FROM {user_input} \n" 
        sock.send(username.encode())
    else: 
        get_valid_username()
    
    return user_input


def connect_and_handshake():
    global connected
    global sock

    while not connected:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(LOCAL_IP_AND_PORT)
        #sock.connect(IP_AND_PORT)

        username = get_valid_username()

        response = sock.recv(BUFFER_SIZE)

        if "HELLO" in response.decode():
            print(GREEN + f"Connected as {username} \n" + RESET_COLOR)
            connected = True
        else:
            print(RED + "Invalid username \n" + RESET_COLOR)
            sock.close() 



def response_handler():
    global buffer_incoming
    global new_data_in_buffer

    while True:
        response = sock.recv(BUFFER_SIZE).decode("utf-8")


        if "DELIVERY" in response:

            responseElements = response.split(" ", 2)
            userName = responseElements[1]
            userMessage = responseElements[2]

            name, message = received_data[9:].strip('\n').split(" ", 1)
                
            recv_checksum = int(response[0:10:])
            recv_id = int(response[10:15:])
            message = response[15:]

            print(RESET_COLOR + userName+": "+ userMessage + RESET_COLOR)
        elif response == "SEND-OK\n":
            print(GREEN + "Message sent successfully\n" + RESET_COLOR)
        elif response == "UNKNOWN\n":
            print(YELLOW + "User doesn't exist\n" + RESET_COLOR)
        elif response == "BAD-RQST-HDR\n":
            print(YELLOW + "Bad Request Header\n" + RESET_COLOR)
        elif response == "BAD-RQST-BODY\n":
            print(YELLOW + "Bad Request Body\n" + RESET_COLOR)
        else:
            print(RESET_COLOR + response + RESET_COLOR)


def send_message(user_input):

    username = user_input.partition(' ')[0][1:]
    message = user_input.partition(' ')[2]
    packet = f"SEND {username} {message}\n" 

    sock.send(packet.encode())


### Creating thread for listener function ###
listener_thread = threading.Thread(target=response_handler, args=())


#### EXECUTION PART ####
try: 
    connect_and_handshake()
    listener_thread.start()
except:
    print(RED + "Failed to connect to server. \n" + RESET_COLOR)

while connected:
    user_input = input(RESET_COLOR)

    if len(user_input) != 0:
        instruction = user_input.partition(' ')[0]

        if instruction == "!quit":
            connected = False
            print(YELLOW + "Connection closed\n" + RESET_COLOR)
        elif instruction == "!who":
            sock.send(("WHO\n").encode())
        elif instruction[0] == "@":
            send_message(user_input)
        elif "SET" in instruction:
            sock.send(user_input.encode())  
        else:
            print(RED + "Invalid instruction. Type '!quit' to exit the script!\n" + RESET_COLOR)
    else:
        pass

os._exit(0)
