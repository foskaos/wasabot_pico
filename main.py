from machine import UART, Pin, ADC, I2C
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

dev = I2C(1, freq=400000,scl=Pin(15),sda=Pin(14))
devices = dev.scan()
for device in devices:
    print(devices)

address = 72


def create_config_string(mux):

    os = '1'
    #mux = '100'
    pga = '001'
    mode = '1'
    dr = '100'
    comp_mode = '0'
    comp_pol = '0'
    comp_lat = '0'
    comp_que = '11'

    #bin_str = os + mux + pga + mode + dr + comp_mode + comp_pol + comp_lat +comp_que
    bin_str = '1' + mux + '001110000011'
    # print('my bin str is ', bin_str)
    cfg = int(bin_str,2)
    # print('made:', bin(int(bin_str, 2)))
    config1 = [int(cfg >> i & 0xFF) for i in (8, 0)]
    #print('config list', config1)
    return config1



def read_config():
    dev.writeto(address, bytearray([1]))
    result = dev.readfrom(address,2)
    #print('reading config returned:', f"{(result[0]):08b}", f"{result[1]:08b}")
    return result[0] << 8 | result[1]


def set_config(mux):
    configur = create_config_string(mux)
    dev.writeto(address, bytearray([1] + configur))
    #print('after setting:: ', bin(read_config()))

def read_value(channel):

    dev.writeto(address,bytearray([0]))
    result = dev.readfrom(address,2)
    config = read_config()
    #print('read config during reading::', bin(config))
    # config &= ~(7<<12) & ~(7<<9)
    # config |= (4<<12) | (1<<9) | (1<<15)
    # config = [int(config >> i & 0xFF) for i in (8,0)]
    # print('after read modifcation: ',config)
    # dev.writeto(address,bytearray([1]+config))
    set_config(channel)
    return result[0] << 8 | result[1]


def val_to_voltage(val,max_val=26100,voltage_ref=3.3):
    return val / max_val * voltage_ref

set_config('111')
while True:
    print('check bit 15')
    rbit = (read_config()>>15)&1
    if rbit:
        break
print('before main loop config read: ', bin(read_config()))

# noinspection PyArgumentList
uart0 = UART(0,
             baudrate=9600,
             tx=Pin(0),
             rx=Pin(1))

print("Sending Messages on Serial port")

uart0.write(GeneralEncoder('pico_join', 'Sending data every 2 seconds').message)
while True:
    print('main loop start')
    set_config('111')
    while True:
        #print('check bit 15')
        rbit = (read_config() >> 15) & 1
        if rbit:
            break
    time.sleep(0.01)
    val = read_value('111')
    print('val1: ',val)
    volts = val_to_voltage(val)
    sensor.measure()  # Recovers measurements from the sensor
    photo = adc.read_u16()
    light = round((1 - photo / 65535) * 100, 2)
    sensor_packet_dict = {'temp': sensor.temperature(),
                          'humidity': sensor.humidity(),
                          'light': light,
                           'voltage':volts
                          }
    sensor_data = SensorEncoder(sensor_packet_dict).message
    uart0.write(sensor_data)
    time.sleep(2)
    set_config('100')
    while True:
        #print('check bit 15')
        rbit = (read_config() >> 15) & 1
        if rbit:
            break
    time.sleep(0.01)
    val2 = read_value('100')
    print('val2: ',val2)
    time.sleep(2)

    volts2 = val_to_voltage(val2)
    sensor_packet_dict2 = {'temp': 0,
                           'humidity': 0,
                           'light': 0,
                           'voltage2': volts2}
    uart0.write(SensorEncoder(sensor_packet_dict2).message)
    print('main loop end')

