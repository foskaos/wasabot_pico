from machine import UART, Pin
import time
import dht

dht_pin=2
sensor = dht.DHT22(Pin(dht_pin))

uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))


class MessageEncoder:
    def __init__(self, message_type, message_data):
        self.message_type = message_type
        self.message = self.encode(message_data)

    def encode(self,message_data):
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def calculate_checksum(data):
        checksum = 0
        for byte in data:
            checksum ^= byte
        return bytes([checksum])

    def make_serial_message(self, data):
        message_type = self.message_type.encode('utf-8')
        m_string = message_type + b':' + data
        cksum = self.calculate_checksum(m_string)
        #print(cksum)
        to_send = b'<' + m_string + cksum + b'>' + b'\n'
        #print(to_send)
        return to_send


class SensorEncoder(MessageEncoder):
    def __init__(self, message_data):
        super().__init__('sensor', message_data)

    def encode(self, message_data):
        enc_data = (':'.join([f"{str(k)}={str(v)}" for k, v in message_data.items()])).encode('utf-8')
        packet = self.make_serial_message(enc_data)
        return packet



class CommandEncoder(MessageEncoder):
    def __init__(self, message_data):
        super().__init__('cmd', message_data)

    def encode(self, message_data):
        packet = self.make_serial_message(message_data)
        return packet


class DataEncoder(MessageEncoder):
    def __init__(self, message_data):
        super().__init__('data', message_data)

    def encode(self, message_data):
        packet = self.make_serial_message(message_data)
        return packet




txData = b'this is a dummy data string for testing'

while True:

    print("Sending Messages on Serial port (dummy data and live DHT-22 Readings")
    message_to_send = DataEncoder(txData).message

    uart0.write(message_to_send)
    time.sleep(2)
    sensor.measure()  # Recovers measurements from the sensor
    sensor_packet_dict = {'temp': sensor.temperature(),
                          'humidity': sensor.humidity()}
    sensor_data = SensorEncoder(sensor_packet_dict).message
    uart0.write(SensorEncoder(sensor_packet_dict).message)
