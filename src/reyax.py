import serial
import time, struct

#OTHER METRICS
def getStartMessage():
    return "bc"

def getNumQuaternions() -> int:
    """
    Modifying this will affect how many quaternions are being sent and recieved on either end
    """
    return 1

def getPackFormat():
    #msb <- lsb
    #h : 2-byte short
    #1 short for time_delta, size = 2-bytes * 4 num on the rest for n=0 -> n=8 (w_n,x_n,y_n,z_n)
    return ">h" + ("hhhh" * getNumQuaternions())

#TIME DELTA (EN/DE)CODING

def time_delta_to_short(time_delta):
    """
    Converts a time_delta with 3 decimal places to a signed 16-bit short.
    The input time_delta must be in seconds and within the range [-32.768, 32.767].
    """
    scaled = int(round(time_delta * 1000))  # Scale
    return max(-32768, min(32767, scaled))  # Clip to 16-bit short range

def short_to_time_delta(short_value):
    """
    Converts a signed 16-bit short back to a time_delta with 2 decimal places.
    """
    return short_value / 1000.0  # Convert back to seconds

#QUATERNION (EN/DE)CODING

def quaternion_to_short(w, x, y, z):
    """
    Converts quaternion (w, x, y, z) components in range [-1, 1]
    to signed 16-bit integers in range [-32768, 32767].
    """
    scale_factor = 32767  # Max value for a signed 16-bit integer

    # Scale and clip values
    def float_to_short(value):
        scaled = int(round(value * scale_factor))
        return max(-32768, min(32767, scaled))  # Clip to 16-bit range

    return [float_to_short(value) for value in (w, x, y, z)]

def short_to_quaternion(w_short, x_short, y_short, z_short):
    """
    Converts signed 16-bit integers in range [-32768, 32767]
    back to quaternion components in range [-1, 1].
    """
    scale_factor = 32767.0  # Max value for scaling
    return [x / scale_factor for x in (w_short, x_short, y_short, z_short)]

#TRANSMISSION DRIVER

class RYLR998:
    def __init__(self, port='/dev/serial0', baudrate=115200, timeout=1, address=1, network_id=1):
        """
        Initialize the serial connection and configure the module's address and network ID if provided.
        """
        
        #all sleeps are threaded in setup_hardware on RPI02W.py

        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        time.sleep(1)  # Allow time for the serial connection to initialize

        self.send_command("AT+RESET")
        time.sleep(2) #Allow time for reset

        # Set configurations to optimal rocket telemetry settings
        self.configure_module()
        
        # Configure network ID if provided
        if network_id is not None:
            print("\nsetting NWID")
            self.set_network_id(network_id)
        
        # Configure address if provided
        if address is not None:
            print("\nsetting ADDR")
            self.set_address(address)

    def configure_module(self):
        """
        Configure the module with hardcoded settings optimal for rocket telemetry
        """

        print("Configuring RYLR998...")

        #Spreading Factor, 9=500kz bw, 2=cr 4/6
        print("AT+PARAMETER", self.send_command('AT+PARAMETER=7,9,2,12'), flush=True)

        # Frequency band: 915 MHz
        print("AT+BAND", self.send_command('AT+BAND=915000000'), flush=True)

        print("AT+MODE", self.send_command('AT+MODE=0'), flush=True) #transmit IMMEDIATELY

        # Transmission power:  20dBm
        print("AT+CRFOP", self.send_command('AT+CRFOP=20'), flush=True)

        print("Config complete.")
    
    def send_command(self, command): #TODO is it more efficient to disregard ser.read and send ignorantly?
        """
        Send an AT command and return the response.
        """
        full_command = f'{command}\r\n'
        self.ser.write(full_command.encode())
        time.sleep(0.05)
        response = ''

        while True:
            if self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting).decode()
                if 'OK' in response or 'ERROR' in response:
                    break
            else:
                break
        response = response.strip()
        if 'ERROR' in response:
            raise RuntimeError(f"Command failed: {command}, Response: {response}")
        
        return response

    def read_decoded_data(self) -> dict:
        """
        DATA FORMAT: +RCV=<Address>,<Length>,<Data>,<RSSI>,<SNR>
        
        <Address> Transmitter Address ID
        <Length> Data Length
        <Data> ASCll Format Data
        <RSSI> Received Signal Strength Indicator
        <SNR> Signal-to-noise ratio

        Read a payload buffer from RPI02W ADDRESS=1, parse by:
        1) decode bytes wt UTF-8 r->l and until you match 2 "," | save start_index = index
        2) decode bytes wt UTF-8 l->r until you match 2 "," | save end_index = index
        3) telemetry_payload = struct.unpack(getPackFormat(), response[start_index:end_index])
        4) format payload to dict & / getMultiplicativeFactor()
        5) voila!
        """

        payload = []

        while True:
            if self.ser.in_waiting:
                response = self.ser.readline()

                if response:

                    start_index, end_index = 0, 0
                    
                    #1
                    comma_ct1 = 0
                    cur_index = 0
                    for byte in response: #type(byte) is int
                        if byte == ord(','):
                            comma_ct1 += 1
                        if comma_ct1 == 2:
                            start_index = cur_index + 1
                            break
                        cur_index += 1
                    
                    #2
                    comma_ct2 = 0
                    cur_index = 0
                    for byte in response[::-1]:
                        if byte == ord(','):
                            comma_ct2 += 1
                        if comma_ct2 == 2:
                            end_index = len(response) - cur_index - 1
                            break
                        cur_index += 1     

                    if comma_ct1 != 2 or comma_ct2 != 2:
                        print("ERROR, cc1:{comma_ct1}, cc2:{comma_ct2}, payload: {response}", flush=True)
                        continue


                    #3
                    data = struct.unpack(getPackFormat(), response[start_index:end_index])

                    #4                    
                    payload.append(short_to_time_delta(data[0])) #time_delta
                    for i in range(1, len(data), 4): #(w_n, x_n, y_n, z_n)
                        quaternion = short_to_quaternion(data[i], data[i+1], data[i+2], data[i+3])
                        payload.append({
                            "rotation_w" : quaternion[0],
                            "rotation_x" : quaternion[1],
                            "rotation_y" : quaternion[2],
                            "rotation_z" : quaternion[3],
                        })
                    
                    #5!
                    return payload
                
                elif response:
                    print(response.decode())

                time.sleep(0.0001)
        

    def send_data(self, data: bytes, dataSize: int, recipient_address: int = 2):
        """
        Send a bytestring to recipient (reciever_address=2 | RPI5) and return the response.
        """
        data = (f"AT+SEND={recipient_address},{dataSize},").encode() + data + "\r\n".encode()
        self.ser.write(data)

        time.sleep(0.01) #TODO rearrange sleep commands for optimal performance
        
        response = ''
        while True:
            if self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting).decode()
                if 'OK' in response or 'ERROR' in response:
                    break
            else:
                break
        
        if 'ERROR' in response:
            raise RuntimeError(f"Command failed: {data}, Response: {response}") #TODO handle for deployment
        
        response = response.strip()
        return response

    def pulse(self):
        """
        Check if the RYLR998 module is responsive by sending a basic AT command.
        Returns True if the module responds with 'OK'.
        """
        response = self.send_command('AT')
        return response

    def set_network_id(self, network_id):
        """
        Set the network ID of the module.
        """

        command = f"AT+NETWORKID={network_id}"
        response = self.send_command(command)
        
        if 'OK' in response:
            print(f"Network ID set to {network_id}", flush=True)
            self.network_id = network_id
        else:
            print(f"Failed to set Network ID: {response}", flush=True)

    def set_address(self, address):
        """
        Set the address of the module.
        """
        
        command = f"AT+ADDRESS={address}"
        response = self.send_command(command)
        
        if 'OK' in response:
            print(f"Address set to {address}", flush=True)
            self.address = address
        else:
            print(f"Failed to set Address: {response}", flush=True)

    def close(self):
        """
        Close the serial connection.
        """
        self.ser.close()
