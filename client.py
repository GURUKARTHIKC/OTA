import socket
import hashlib
import os
import threading

FIRMWARE_FILE = "car_firmware.bin"
CAR_PORT = 65433  # Listening port for other cars
SERVER_IP = "192.168.1.1"  # Change this to the server's IP
SERVER_PORT = 65432


def generate_checksum(file_path):
    """Generate SHA-256 checksum for a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


def listen_for_server_updates():
    """Listen for update notifications from the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", CAR_PORT))
        s.listen()
        print("Listening for updates from the server...")

        while True:
            conn, addr = s.accept()
            with conn:
                message = conn.recv(1024).decode()
                if message == "UPDATE_AVAILABLE":
                    print("Update available from server. Downloading...")
                    receive_firmware_from_server()


def receive_firmware_from_server():
    """Connect to the server and receive a firmware update with resume support."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_IP, SERVER_PORT))
            received = os.path.getsize(FIRMWARE_FILE) if os.path.exists(FIRMWARE_FILE) else 0
            s.sendall(str(received).encode())
            metadata = s.recv(1024).decode()
            checksum, file_size = metadata.split(":")
            file_size = int(file_size)
            s.sendall("ACK_METADATA".encode())

            with open(FIRMWARE_FILE, 'ab' if received > 0 else 'wb') as f:
                while received < file_size:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            if generate_checksum(FIRMWARE_FILE) == checksum:
                print("Server firmware update successful!")
            else:
                print("Checksum mismatch! Update may be corrupted.")
        except Exception as e:
            print(f"Error receiving firmware from server: {e}")


def start_p2p_listening():
    """Start listening for firmware requests from peer cars."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", CAR_PORT))
        s.listen()
        print(f"Car listening for firmware requests on port {CAR_PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected to peer car at {addr}")
                peer_data = conn.recv(1024).decode()
                peer_checksum, received_bytes = peer_data.split(":")
                received_bytes = int(received_bytes)

                local_checksum = generate_checksum(FIRMWARE_FILE)
                file_size = os.path.getsize(FIRMWARE_FILE)
                conn.sendall(f"{local_checksum}:{file_size}".encode())

                request = conn.recv(1024).decode()
                if request == "REQUEST_UPDATE":
                    send_firmware_to_peer(conn, received_bytes)


def send_firmware_to_peer(conn, received):
    """Send firmware update to the peer car, resuming if necessary."""
    with open(FIRMWARE_FILE, 'rb') as f:
        f.seek(received)
        while chunk := f.read(4096):
            conn.sendall(chunk)
    print("Firmware sent to peer car!")


if __name__ == "__main__":
    threading.Thread(target=listen_for_server_updates, daemon=True).start()
    threading.Thread(target=start_p2p_listening, daemon=True).start()
    print("Client is running and ready for updates...")
