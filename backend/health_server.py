#!/usr/bin/env python3
import socket
import sys

def run_server():
    # Create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8000))
    server.listen(1)
    
    print("Server listening on port 8000...", flush=True)
    sys.stdout.flush()
    
    while True:
        try:
            client, addr = server.accept()
            request = client.recv(1024).decode('utf-8', errors='ignore')
            
            response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 75\r\n\r\n{\"status\":\"healthy\",\"app\":\"Viral Video SaaS\",\"version\":\"1.0.0\"}"
            client.sendall(response)
            client.close()
        except Exception as e:
            print(f"Error: {e}", flush=True)
            continue

if __name__ == "__main__":
    run_server()
