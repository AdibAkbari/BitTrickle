# BitTrickle: Peer-to-Peer File Sharing Application

## Overview
BitTrickle is a lightweight, decentralized peer-to-peer (P2P) file sharing program that allows clients to share files directly with each other over a network, managed by a central authentication and discovery server. Built in Python, it provides a simple and efficient way for users to publish, search, and download files across a local network.

## Features
- User authentication with secure credentials
- Peer discovery and file search functionality
- Direct peer-to-peer file transfers
- Multi-threaded architecture for concurrent operations
- Simple command-line interface

## Design and Architecture
### Server Components
- Manages user authentication
- Tracks active peers and their published files
- Acts as a directory service for file discovery
- Monitors client activity through periodic heartbeats

### Client Components
- Authentication and network communication
- Multi-threaded design supporting:
  - Heartbeat thread (maintains active status)
  - User input thread (handles commands)
  - Download listening thread (manages file transfer requests)

### Network Communication 
  - UDP for server communication
  - TCP for direct file transfers

### Libraries: 
  - `socket` for network programming
  - `threading` for concurrent operations
  - `os` for file and directory management

## Supported Commands
- `lap`: List active peers
- `lpf`: List published files
- `pub <filename>`: Publish a file
- `unp <filename>`: Unpublish a file
- `sch <substring>`: Search for files
- `get <filename>`: Download a file
- `xit`: Exit the application

## Prerequisites
- Python 3.x
- A `credentials.txt` file with username and password entries

## Usage

### Server Setup
1. Ensure a `credentials.txt` file is in the same directory where you execute server.py. 
2. Run the server:
```bash
python3 server.py <server_port>
```

### Client Setup
1. Navigate to the directory containing your files
2. Run the client:
```bash
python3 ~/path/to/client.py <server_port>
```
3. Log in with credentials from `credentials.txt`
4. Use available commands to interact with the network
5. Join with more clients to share publish and share files between clients.

## Limitations
- Requires manual directory setup for each user
- Basic error handling
- Assumes unique file names
- Limited to local network operations

