import socket
import threading 
import time
import binascii
import random
import os

### TERMINAL COLORS
GREEN = "\033[92m"
YELLOW = "\033[93m" 
RED = "\033[91m" 
BLUE = '\033[94m'
RESET_COLOR = "\033[0m" 

IP_AND_PORT = "3.121.226.198", 5382
BUFFER_SIZE = 2000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

connected = False

pending_ack = {}
pending_sync_ack = {}

unknown_message_destination = False

received_contacts = {}
send_contacts = {}

#################################################################################

def get_valid_username():
    user_input = input("Please enter your username: ")

    if len(user_input) != 0:
        username = user_input 
    else: 
        get_valid_username()
    
    return username


def packet_formatting(username, id, message):
    crc_code = binascii.crc32(bytes((format(id, '05d') + message), "utf-8"))

    package = f"SEND {username} {format(crc_code, '010d')} {format(id, '05d')} {message}\n"

    return package


def user_sync(username, id=-1):
    global pending_sync_ack
    global unknown_message_destination

    if id == None:
        id = random.randint(0, 3000)
    
    pending_sync_ack[username] = id

    attempts = 0

    while username in pending_sync_ack:
        attempts += 1

        print(YELLOW + "Establishing connection" + RESET_COLOR, end = "\r")

        sock.send(packet_formatting(username, id, "SYNC").encode())

        time.sleep(0.20)

        if unknown_message_destination:
            print(RED + "Message destionation doesn't exist" + RESET_COLOR)
            del pending_sync_ack[username]

            #### Reset global variable
            unknown_message_destination = False

            return False

        elif attempts == 10:
            print(RED + "Unable to reach message destionation" + RESET_COLOR)
            del received_contacts[username]
            return False
    
    return True
    

def incoming_data_handler():
    global unknown_message_destination

    while True:
        try:
            received_data = sock.recv(BUFFER_SIZE).decode()
            received_list = received_data.split()

            server_message = received_list[0]

            if server_message == "DELIVERY":

                username = received_list[1]
                recv_crc_code = int(received_list[2])
                recv_id = int(received_list[3])
                message = " ".join(received_list[4:])
        
                crc_code = binascii.crc32(bytes((format(recv_id, '05d') + message), 'utf-8'))

                ######### CRC code check ####### might add crc counter that will display if there are too many mismatches
                if  recv_crc_code != crc_code:          
                    continue

                if message == "ACK":
                    if send_contacts[username] == recv_id and username in pending_ack:
                        print(GREEN + "Message successfully delivered      " + RESET_COLOR)
                        del pending_ack[username]
                        send_contacts[username] = send_contacts[username] + 1

                    continue

                elif message == "SYNC":
                    received_contacts[username] = recv_id
                    sock.send(packet_formatting(username, recv_id, "SYNC-ACK").encode())

                    continue

                elif message == "SYNC-ACK":
                    if username in pending_sync_ack:
                        send_contacts[username] = recv_id
                        del pending_sync_ack[username]

                    continue

                elif message == "RESYNC":
                    #Thread(target = user_sync, args = ()).start()
                    user_sync(username)

                    continue

                elif not username in received_contacts:
                    sock.send(packet_formatting(username, 0, "RESYNC").encode())

                    continue

                elif recv_id != received_contacts[username]:
                    prev_id = received_contacts[username] - 1

                    if recv_id == prev_id:
                        print("")
                        sock.send(packet_formatting(username, prev_id, "ACK").encode())
                    
                    else:
                        print("Resync requested")
                        sock.send(packet_formatting(username, 0, "RESYNC").encode())

                    continue
                
                sock.send(packet_formatting(username, recv_id, "ACK").encode())

                #### PRINTING MESSAGE ####
                print(f"{RESET_COLOR}{username}: {message}")

                received_contacts[username] += 1

            elif received_data == "UNKNOWN\n":
                unknown_message_destination = True
                continue

        except:
            continue


def send_packet(username, msg):
    global unknown_message_destination

    if not username in send_contacts:
        if not user_sync(username):
            return

    pending_ack[username] = send_contacts[username]
    
    attempts = 0
    while username in pending_ack:
        while username in pending_sync_ack:
            time.sleep(0.25)

        print(YELLOW + "Reaching message destination", end = "\r" + RESET_COLOR)

        sock.send(packet_formatting(username, send_contacts[username], msg).encode())

        time.sleep(0.20)

        if unknown_message_destination:
            print(RED + "User doesn't exist               " + RESET_COLOR)
            del pending_ack[username]
            del send_contacts[username]

            #### Reset global variable
            unknown_message_destination = False

            return

        attempts += 1
    
        if attempts == 20:
            try:
                del send_contacts[username]
            except:
                pass
            try:
                del received_contacts[username]
            except:
                pass

            print(RED + "Failed to send message      " + RESET_COLOR)
            return

 
def connect_and_handshake():
    global connected
    global sock

    while not connected:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(IP_AND_PORT)

        username = get_valid_username()

        sock.send((f"HELLO-FROM {username}\n").encode())
        #sock.send(("SET FLIP 0.4").encode())

        response = sock.recv(BUFFER_SIZE).decode()

        if "HELLO" in response:
            
                print(GREEN + f"Connected as {username} \n" + RESET_COLOR)
                connected = True
        else:
            print(RED + "Invalid username \n" + RESET_COLOR)
            sock.close()


listener_thread = threading.Thread(target=incoming_data_handler, args=())

#################################################################################

#### EXECUTION PART ####
try: 
    connect_and_handshake()
    listener_thread.start()
except socket.error as e:
    print(RED + "Failed to connect to server. \n" + RESET_COLOR)
    print("Socket error:" + e)

while connected:
    user_input = input(RESET_COLOR)
    


    if len(user_input) != 0:
        instruction = user_input.partition(' ')[0]

        if instruction == "!quit":
            #sock.send(("!quit").encode())
            #sock.close()
            connected = False
            print(YELLOW + "Connection closed\n" + RESET_COLOR)

        elif instruction == "!who":
            sock.send(("WHO\n").encode())
            connected_users = {}
            connected_users.update(received_contacts) 
            connected_users.update(send_contacts) 
            print(f"{BLUE}active users: {list(connected_users.keys())}{RESET_COLOR}")

        elif instruction[0] == "@":
            username = user_input.partition(' ')[0][1:]
            message = user_input.partition(' ')[2]

            send_packet(username, message)  
        else:
            print(RED + "Invalid instruction. Type '!quit' to exit the script!\n" + RESET_COLOR)
    else:
        pass

os._exit(0)

