import os

FIRMWARE_FILE = "firmware_update.bin"
FIRMWARE_SIZE = 1024 * 500  # 500KB firmware size (adjust as needed)

def create_firmware_update():
    """Create a sample firmware update file for testing."""
    with open(FIRMWARE_FILE, 'wb') as f:
        f.write(os.urandom(FIRMWARE_SIZE))  # Generate random binary data
    print(f"Firmware update file '{FIRMWARE_FILE}' created with size {FIRMWARE_SIZE} bytes.")

if __name__ == "__main__":
    create_firmware_update()
