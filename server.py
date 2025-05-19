import socket
import hashlib
import os
import threading

FIRMWARE_FILE = "firmware_update.bin"
SERVER_PORT = 65432
CLIENT_PORT = 65433  # Port on which clients listen for update notifications


def generate_checksum(file_path):
    """Generate SHA-256 checksum for a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


def notify_clients(client_ips):
    """Send update notifications to all known clients."""
    for client_ip in client_ips:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client_ip, CLIENT_PORT))  # Directly connect to the client
                s.sendall("UPDATE_AVAILABLE".encode())
                print(f"Notified client {client_ip}")
        except Exception as e:
            print(f"Failed to notify {client_ip}: {e}")



def start_server():
    """Start the OTA update server and handle client connections."""
    if not os.path.exists(FIRMWARE_FILE):
        print("Firmware file not found. Server cannot start.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", SERVER_PORT))
        s.listen()
        print(f"Server listening on port {SERVER_PORT}...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()


def handle_client(conn, addr):
    """Handle firmware transfer for a connected client."""
    with conn:
        print(f"Connected to client at {addr}")

        # Receive how much the client has already downloaded
        received = int(conn.recv(1024).decode())
        print(f"Client has received {received} bytes.")

        # Get file details
        checksum = generate_checksum(FIRMWARE_FILE)
        file_size = os.path.getsize(FIRMWARE_FILE)

        # Send metadata (checksum + file size)
        conn.sendall(f"{checksum}:{file_size}".encode())

        # Wait for acknowledgment
        ack = conn.recv(1024).decode()
        if ack != "ACK_METADATA":
            print("Metadata acknowledgment failed.")
            return

        # Send firmware data starting from where the client left off
        with open(FIRMWARE_FILE, 'rb') as f:
            f.seek(received)
            while chunk := f.read(4096):
                conn.sendall(chunk)

        print("Firmware sent successfully.")


if __name__ == "__main__":
    threading.Thread(target=notify_clients, daemon=True).start()
    start_server()
