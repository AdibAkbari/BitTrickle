#!/usr/bin/python3

# server.py
import socket
import sys
import time
import threading

# Load credentials function as defined before
def load_credentials():
    credentials = {}
    with open("credentials.txt", "r") as file:
        for line in file:
            username, password = line.strip().split()
            credentials[username] = password
    return credentials

# Check for the correct number of command-line arguments
if len(sys.argv) != 2:
    print("Usage: python3 server.py <server_port>")
    sys.exit(1)

# Set up the server port and load credentials
server_port = int(sys.argv[1])
credentials = load_credentials()
active_clients = {}  # Dictionary to track active clients by client address
published_files = {}  # Dictionary to track published files for each user
client_ports = {} # Dictionary to track TCP ports of active clients
exit_event = threading.Event()  # Event to control graceful exit across threads

# Create a UDP socket for the server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("127.0.0.1", server_port))
print(f"Server is running on port {server_port} and waiting for client connections...")

# Function to handle heartbeats and remove inactive clients
def check_inactive_clients():
    while not exit_event.is_set():
        current_time = time.time()
        inactive_clients = [client for client, (_, last_time) in active_clients.items() if current_time - last_time > 3]
        
        for client in inactive_clients:
            username, _ = active_clients.pop(client)  # Remove user from active clients
            client_ports.pop(username, None)
            print(f"Client {client} with username '{username}' has been marked inactive and removed from active clients.")
        
        time.sleep(1)

# Start a background thread to check inactive clients
threading.Thread(target=check_inactive_clients, daemon=True).start()

try:
    # Main server loop to handle incoming messages
    while not exit_event.is_set():
        message, client_address = server_socket.recvfrom(1024)
        decoded_message = message.decode()
        print(f"Received message from {client_address}: {decoded_message}")
        
        # Authentication handling
        if decoded_message.startswith("AUTH"):
            _, username, password, tcp_port = decoded_message.split()
            tcp_port = int(tcp_port)
            
            # Check if user is already active
            if any(user == username for user, _ in active_clients.values()):
                response = "USER_ALREADY_ACTIVE"
            elif username in credentials and credentials[username] == password:
                response = "AUTH_SUCCESS"
                active_clients[client_address] = (username, time.time())  # Add client to active clients with timestamp
                client_ports[username] = tcp_port
                print(f"User '{username}' authenticated successfully from {client_address}")
            else:
                response = "AUTH_FAILURE"
            
            # Send response to the client
            server_socket.sendto(response.encode(), client_address)
        
        # Heartbeat handling
        elif decoded_message == "HEARTBEAT":
            if client_address in active_clients:
                username, _ = active_clients[client_address]
                active_clients[client_address] = (username, time.time())  # Update last heartbeat timestamp
                print(f"Received heartbeat from {username} at {client_address}")

        # Handle client commands
        elif decoded_message == "lap":
            # Return list of active users excluding the requesting client
            username, _ = active_clients[client_address]
            active_users = [user for client, (user, _) in active_clients.items() if client != client_address]
            response = "No active peers" if not active_users else "Active peers: " + ", ".join(active_users)
            server_socket.sendto(response.encode(), client_address)
        
        elif decoded_message == "lpf":
            # Return list of files published by the requesting user
            username, _ = active_clients[client_address]
            user_files = published_files.get(username, [])
            response = "No files published" if not user_files else "Published files: " + ", ".join(user_files)
            server_socket.sendto(response.encode(), client_address)
        
        elif decoded_message.startswith("pub"):
            msg_parts = decoded_message.split(" ")
            filename = msg_parts[1].strip()
            username, _ = active_clients[client_address]
            user_files = published_files.get(username, [])
            if len(user_files) == 0:
                published_files[username] = [filename]
                response = f"Published file: {filename}"
            else:
                # only adds file if not already published by user
                if filename in user_files:
                    response = f"Already published file: {filename}"
                else:
                    published_files[username].append(filename)
                    response = f"Published file: {filename}"
            print(published_files)
            server_socket.sendto(response.encode(), client_address)
            
        elif decoded_message.startswith("unp"):
            msg_parts = decoded_message.split(" ")
            filename = msg_parts[1].strip()
            username, _ = active_clients[client_address]
            user_files = published_files.get(username, [])
            if filename in user_files:
                # remove file
                published_files[username].remove(filename)
                response = f"Unpublished file: {filename}"
            else:
                response = f"User has not published file: {filename}"
            print(published_files)
            server_socket.sendto(response.encode(), client_address)
        elif decoded_message.startswith("sch "):
            msg_parts = decoded_message.split(" ")
            substring = msg_parts[1].strip()
            username, _ = active_clients[client_address]

            # get all active client names excluding this client
            other_active_users = []
            for key, value in active_clients.items():
                curr_username, _ = value
                print(curr_username)
                if (curr_username != username):
                    other_active_users.append(curr_username)

            # search published files of all other_active_users for files matching substring
            matching_files = []
            for curr_user in other_active_users:
                if published_files.get(curr_user, []):
                    for filename in published_files[curr_user]:
                        if substring in filename:
                            matching_files.append(filename)
            
            # filter out duplicates
            matching_files = list(set(matching_files))

            # filter out files also published by this user
            matching_files = [file for file in matching_files if file not in published_files.get(username, [])]
            
            response = " | ".join(matching_files)
            server_socket.sendto(response.encode(), client_address)
            
        elif decoded_message.startswith("get"):
            filename = decoded_message.split(" ", 1)[1]
            file_owner = None

            # Find an active client who has published the requested file
            for user, files in published_files.items():
                if filename in files and user in client_ports:
                    file_owner = user
                    break

            if file_owner:
                # Send the IP and TCP port of the owner to the requesting client
                owner_addr = next(addr for addr, (uname, _) in active_clients.items() if uname == file_owner)
                response = f"{owner_addr[0]} {client_ports[file_owner]}"
            else:
                response = "File not found"
            server_socket.sendto(response.encode(), client_address)            

except KeyboardInterrupt:
    print("\nServer interrupted with Ctrl+C, exiting gracefully...")
finally:
    exit_event.set()  # Signal all threads to stop
    server_socket.close()
    print("Server has closed the connection.")

