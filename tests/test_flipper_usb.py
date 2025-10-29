import logging
from src.device.flipper_usb import FlipperUSB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    flipper = FlipperUSB()
    
    # Find available Flipper Zero devices
    ports = flipper.find_flipper_ports()
    if not ports:
        print("No Flipper Zero USB devices found!")
        return
        
    print(f"Found Flipper Zero ports: {ports}")
    port = ports[0]
    
    # Try to connect
    if flipper.connect(port):
        print(f"Successfully connected to Flipper Zero on {port}")
        
        # Send a test command (simple ping)
        test_command = b'\x01'
        if flipper.send_command(test_command):
            print("Test command sent successfully")
            
            # Read response
            response = flipper.read_response()
            if response:
                print(f"Received response: {response.hex()}")
        
        flipper.disconnect()
        print("Disconnected")
    else:
        print("Failed to connect!")

if __name__ == "__main__":
    main()