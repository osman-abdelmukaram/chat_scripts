import socket 
import threading
import os
import time 

## CONSOLE COLORS
GREEN = "\033[92m"
YELLOW = "\033[93m" 
RED = "\033[91m" 
RESET_COLOR = "\033[0m"

IP = socket.gethostbyname(socket.gethostname())
PORT = 5378
BUFFER_SIZE = 4096 
ADDRESS = IP, PORT

TRAFFIC = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(ADDRESS)

active_usernames = []
connected_clients = {}


def client_handler(connection):
    global active_usernames

    i = 0

    #username = connection.recv(BUFFER_SIZE).decode("utf-8")
    #username = username.partition(' ')[2].replace(" \n","")

    username = connection.recv(BUFFER_SIZE).decode("utf-8").partition(' ')[2].replace(" \n","")

    if username in active_usernames:
        connection.send(("IN-USE").encode("utf-8"))
        connection.close()
        connected = False
    else:
        connection.send((f"HELLO {username} \n").encode())
        active_usernames.append(username)
        connected = True

    ## Add user to dictionary | key = [username], value = [socket]
    connected_clients[username] = connection

    while connected:
        try:
            if i == 200:
                print ("too much traffic")

            instruction = connection.recv(BUFFER_SIZE).decode("utf-8")
            i = i + 1
            print(i)
            client_instruction_handler(instruction, connection)

        except:
            print(f"Connection with {username} closed\n")
            del connected_clients[username]
            connection.close()
            return


def client_instruction_handler(instruction, connection):

    if instruction == "WHO\n":
        connection.send((f"WHO-OK: {str(active_usernames)[1:-1]} \n").encode("utf-8"))
    elif "SEND" in instruction:
        username = instruction.split()[1]
        message = instruction.split()[2]
    
        try:
            send(username, message)
            connection.send(("SEND-OK\n").encode())
        except:
            connection.send(("UNKNOWN\n").encode())
    else:
        pass
        


def send(username, message):
    connected_clients[username].send((username + ": " + message).encode("utf-8"))


def start_server():
    ### Will accept up to 60 connections
    sock.listen(60)
    listening = True

    print(f"Server listening at: IP_ADDRESS: {IP}, PORT: {PORT} ")

    while listening:
        connection, client_address = sock.accept()

        handler_thread = threading.Thread(target=client_handler, args=(connection))
        handler_thread.start()

        #client_spammer = threading.Thread(target=spammer, args=( ))
        #client_spammer.start()

#################
#################
start_server()