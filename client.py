#!/usr/bin/python3

# client.py
import socket
import sys
import threading
import time
import os

# Check for the correct number of command-line arguments
if len(sys.argv) != 2:
    print("Usage: python3 client.py <server_port>")
    sys.exit(1)

# Set up the server address from command-line argument
server_port = int(sys.argv[1])
server_address = ("127.0.0.1", server_port)

# Create a UDP socket for the client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# TCP socket for file transfers
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind(('', 0))  # Bind to an available port
tcp_port = tcp_socket.getsockname()[1]  # Get the allocated port number
tcp_socket.listen(5)  # Listen for incoming connections

# Global variables to track authentication status and exit state
authenticated = False
authenticated_username = None
exit_event = threading.Event()  # Event to control graceful exit across threads

# Function to send heartbeat messages periodically
def send_heartbeat():
    global authenticated
    while authenticated and not exit_event.is_set():
        time.sleep(2)
        try:
            client_socket.sendto("HEARTBEAT".encode(), server_address)
        except Exception as e:
            print(f"Error sending heartbeat: {e}")
            break

def download_file(ip, port, filename):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.connect((ip, port))
        tcp_socket.send(filename.encode())  # Send filename request
        
        with open(filename, "wb") as file:
            while True:
                data = tcp_socket.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"Downloaded {filename} successfully.")

# Listening for file requests from other clients
def listen_for_download_requests():
    while not exit_event.is_set():
        client_conn, addr = tcp_socket.accept()
        threading.Thread(target=handle_file_upload, args=(client_conn,), daemon=True).start()

def handle_file_upload(client_conn):
    filename = client_conn.recv(1024).decode()
    if os.path.isfile(filename):
        with open(filename, "rb") as file:
            while (data := file.read(1024)):
                client_conn.send(data)
    client_conn.close()

# Function to handle user input in a command-line style interface
def handle_user_input():
    global authenticated
    while authenticated and not exit_event.is_set():
        try:
            command = input("> ")  # Command prompt
        except EOFError:
            # Handle Ctrl+D (EOF) for graceful exit
            print("\nExiting gracefully...")
            exit_event.set()  # Signal all threads to exit
            authenticated = False
            break
        
        if command == "exit" or command == "xit":
            print("Exiting gracefully...")
            exit_event.set()  # Signal all threads to exit
            authenticated = False
            break
        elif command == "lap":
            client_socket.sendto(command.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            print(response.decode())
        elif command == "lpf":
            client_socket.sendto(command.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            print(response.decode())
        elif command.startswith("pub"):
            parts = command.split(" ")
            if parts[0] != "pub":
                print("Unknown command")
                continue
            if len(parts) != 2 or parts[1] == "" or parts[1] == " ":
                print("Usage: pub <filename>")
                continue
            filename = parts[1].strip()

            if not os.path.isfile(filename):
                print(f"Error: The file '{filename}' does not exist in this user's directory")
                continue
            pub_message = f"pub {filename}"
            client_socket.sendto(pub_message.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            print(response.decode())
        elif command.startswith("unp"):
            parts = command.split(" ")
            if parts[0] != "unp":
                print("Unknown command")
                continue
            if len(parts) != 2 or parts[1] == "" or parts[1] == " ":
                print("Usage: unp <filename>")
                continue
            filename = parts[1].strip()

            unp_message = f"unp {filename}"
            client_socket.sendto(unp_message.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            print(response.decode())
        elif command.startswith("sch"):
            parts = command.split(" ")
            if parts[0] != "sch":
                print("Unknown command")
                continue
            if len(parts) != 2 or parts[1] == "" or parts[1] == " ":
                print("Usage: sch <substring>")
                continue
            substring = parts[1].strip()

            sch_message = f"sch {substring}"

            client_socket.sendto(sch_message.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            response_decoded = response.decode()
            if response_decoded == "":
                print("No files found")
                continue
            

            files = response_decoded.split(" | ")
            num_files = len(files)
            if num_files == 1:
                print("1 file found:")
            else:
                print(f"{num_files} files found:")
                
            for file in files:
                print(file.strip())

        elif command.startswith("get"):
            parts = command.split(" ")
            if parts[0] != "get":
                print("Unknown command")
                continue
            if len(parts) != 2 or parts[1] == "" or parts[1] == " ":
                print("Usage: get <filename>")
                continue
            filename = parts[1].strip()

            get_message = f"get {filename}"
            client_socket.sendto(get_message.encode(), server_address)
            response, _ = client_socket.recvfrom(1024)
            if response.decode() == "File not found":
                print("File not found on active peers.")
            else:
                # Extract IP and port and start TCP connection
                peer_ip, peer_port = response.decode().split()
                download_file(peer_ip, int(peer_port), filename)        
        
        else:
            print("Unknown command")

# Authentication loop
while not authenticated and not exit_event.is_set():
    # Prompt for username and password for authentication
    username = input("Enter username: ")
    password = input("Enter password: ")
    auth_message = f"AUTH {username} {password} {tcp_port}"
    client_socket.sendto(auth_message.encode(), server_address)

    response, _ = client_socket.recvfrom(1024)
    decoded_response = response.decode()

    if decoded_response == "AUTH_SUCCESS":
        print("Welcome to BitTrickle!")
        print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
        authenticated = True
        authenticated_username = username

        # Start the heartbeat thread
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        # Start the user input thread
        user_input_thread = threading.Thread(target=handle_user_input, daemon=True)
        user_input_thread.start()
        
        # Start the download listen thread
        download_listen_thread = threading.Thread(target=listen_for_download_requests, daemon=True)
        download_listen_thread.start()
        
        # Keep the main thread alive to allow the daemon threads to continue
        user_input_thread.join()
    elif decoded_response == "USER_ALREADY_ACTIVE":
        print("User is already active. Please try with a different username.")
    else:
        print("Authentication failed! Please try again.")

# Cleanup on exit
client_socket.close()
tcp_socket.close()
print("Client has closed the connection.")
