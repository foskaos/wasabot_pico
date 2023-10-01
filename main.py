from machine import UART, Pin, ADC
import time
import dht

class MessageEncoder:
    def __init__(self, message_type, message_data):
        self.message_type = message_type
        self.message = self.encode(message_data)

    def encode(self, message_data):
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
        to_send = b'<' + m_string + cksum + b'>' + b'\n'
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

class GeneralEncoder(MessageEncoder):
    def __init__(self, message_type, message_data):
        super().__init__(message_type, message_data)

    def encode(self, message_data):
        packet = self.make_serial_message(message_data)
        return packet


class DataEncoder(MessageEncoder):
    def __init__(self, message_data):
        super().__init__('data', message_data)

    def encode(self, message_data):
        packet = self.make_serial_message(message_data)
        return packet

dht_pin = 2
sensor = dht.DHT22(Pin(dht_pin))

adc = ADC(Pin(26))
# noinspection PyArgumentList
uart0 = UART(0,
             baudrate=9600,
             tx=Pin(0),
             rx=Pin(1))

print("Sending Messages on Serial port")

uart0.write(GeneralEncoder('pico_join', 'Sending data every 2 seconds').message)
while True:
    sensor.measure()  # Recovers measurements from the sensor
    photo = adc.read_u16()
    light = round((1 - photo / 65535) * 100, 2)
    sensor_packet_dict = {'temp': sensor.temperature(),
                          'humidity': sensor.humidity(),
                          'light': light}
    sensor_data = SensorEncoder(sensor_packet_dict).message
    uart0.write(SensorEncoder(sensor_packet_dict).message)
    time.sleep(2)
