"""Quick Flipper Zero USB detection and connection test."""
import serial
import serial.tools.list_ports
import time

# Flipper Zero USB VID/PID combinations
FLIPPER_DEVICES = [
    (0x0483, 0x5740),  # Standard CDC mode
    (0x0483, 0xdf11),  # DFU mode
    (0x0483, 0x5741),  # CLI mode
    (0x0483, 0x5742),  # Serial mode
]

def find_flipper():
    """Find Flipper Zero COM port."""
    print("\nScanning for USB devices...")
    for port in serial.tools.list_ports.comports():
        print(f"\nFound device: {port.device}")
        print(f"Description: {port.description}")
        print(f"Hardware ID: {port.hwid}")
        print(f"VID:PID = {port.vid:04x}:{port.pid:04x}")
        
        # Check if this is a Flipper Zero in any mode
        for vid, pid in FLIPPER_DEVICES:
            if port.vid == vid and port.pid == pid:
                print("\nThis appears to be a Flipper Zero!")
                return port.device
    return None

def main():
    print("Scanning for Flipper Zero...")
    port = find_flipper()
    
    if not port:
        print("No Flipper Zero found! Please check:")
        print("1. Flipper Zero is connected via USB")
        print("2. Flipper Zero is powered on")
        print("3. You're using a data-capable USB cable")
        return
    
    print(f"\nFound Flipper Zero on {port}")
    print("Attempting to connect...")
    
    try:
        print("\nAttempting to open serial connection...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        print(f"Connected to {port}")
        
        # Send device info request
        print("\nSending info request...")
        ser.write(b'device_info\r\n')
        time.sleep(0.5)
        
        # Read response
        print("Waiting for response...")
        attempts = 5
        while attempts > 0:
            if ser.in_waiting:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    print(f"Received: {response}")
            else:
                attempts -= 1
                time.sleep(0.5)
                
        if attempts == 0:
            print("\nNo response received. Please check:")
            print("1. CLI is enabled in Flipper's Settings -> System")
            print("2. Debug UART is enabled")
            print("3. Flipper is showing the CLI prompt")
        
        ser.close()
        print("\nConnection closed")
        
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure no other program is using the port")
        print("2. Try disconnecting and reconnecting the USB cable")
        print("3. Check if Flipper Zero is in the correct mode")

if __name__ == "__main__":
    main()