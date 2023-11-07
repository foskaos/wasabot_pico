from machine import UART, Pin, ADC, I2C
import time
import dht
from test_module import printa
from states_mach import PumpState,PumpStateMachine,ReservoirState,ReservoirStateMachine,Irrigator,DeviceCommand,CommandStatus
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

# dev = I2C(1, freq=400000,scl=Pin(15),sda=Pin(14))
# devices = dev.scan()
# for device in devices:
#     print(devices)
#
# address = 72

class ADS1115:

    def __init__(self,address):
        self.address = address
        self.dev = I2C(1, freq=400000, scl=Pin(15), sda=Pin(14))
        devices = self.dev.scan()
        for device in devices:
            print(devices)

        self.set_config('111')
        self.check_ready()

    def create_config_string(self,mux):
        os = '1'
        # mux = '100'
        pga = '001'
        mode = '1'
        dr = '100'
        comp_mode = '0'
        comp_pol = '0'
        comp_lat = '0'
        comp_que = '11'

        # bin_str = os + mux + pga + mode + dr + comp_mode + comp_pol + comp_lat +comp_que
        bin_str = '1' + mux + '001110000011'
        # print('my bin str is ', bin_str)
        cfg = int(bin_str, 2)
        # print('made:', bin(int(bin_str, 2)))
        config1 = [int(cfg >> i & 0xFF) for i in (8, 0)]
        # print('config list', config1)
        return config1

    def read_config(self):
        self.dev.writeto(self.address, bytearray([1]))
        result = self.dev.readfrom(self.address, 2)
        # print('reading config returned:', f"{(result[0]):08b}", f"{result[1]:08b}")
        return result[0] << 8 | result[1]

    def check_ready(self):
        while True:
            # print('check bit 15')
            rbit = (self.read_config() >> 15) & 1
            if rbit:
                break

    def set_config(self,mux):
        configur = self.create_config_string(mux)
        self.dev.writeto(self.address, bytearray([1] + configur))
        # print('after setting:: ', bin(read_config()))

    def read_value(self,channel):
        self.dev.writeto(self.address, bytearray([0]))
        result = self.dev.readfrom(self.address, 2)
        config = self.read_config()
        # print('read config during reading::', bin(config))
        # config &= ~(7<<12) & ~(7<<9)
        # config |= (4<<12) | (1<<9) | (1<<15)
        # config = [int(config >> i & 0xFF) for i in (8,0)]
        # print('after read modifcation: ',config)
        # dev.writeto(address,bytearray([1]+config))
        self.set_config(channel)
        return result[0] << 8 | result[1]

    def read_adc_from_channel(self, channel):

        self.set_config(channel)
        while True:
            rbit = (self.read_config() >> 15) & 1
            if rbit:
                break
        # time.sleep(0.01)
        adc_val = self.read_value(channel)
        return adc_val

    @staticmethod
    def val_to_voltage(val, max_val=26100, voltage_ref=3.3):
        return val / max_val * voltage_ref


# def create_config_string(mux):
#
#     os = '1'
#     #mux = '100'
#     pga = '001'
#     mode = '1'
#     dr = '100'
#     comp_mode = '0'
#     comp_pol = '0'
#     comp_lat = '0'
#     comp_que = '11'
#
#     #bin_str = os + mux + pga + mode + dr + comp_mode + comp_pol + comp_lat +comp_que
#     bin_str = '1' + mux + '001110000011'
#     # print('my bin str is ', bin_str)
#     cfg = int(bin_str,2)
#     # print('made:', bin(int(bin_str, 2)))
#     config1 = [int(cfg >> i & 0xFF) for i in (8, 0)]
#     #print('config list', config1)
#     return config1
#
#
# def read_config():
#     dev.writeto(address, bytearray([1]))
#     result = dev.readfrom(address,2)
#     #print('reading config returned:', f"{(result[0]):08b}", f"{result[1]:08b}")
#     return result[0] << 8 | result[1]
#
#
# def set_config(mux):
#     configur = create_config_string(mux)
#     dev.writeto(address, bytearray([1] + configur))
#     #print('after setting:: ', bin(read_config()))
#
#
# def read_value(channel):
#
#     dev.writeto(address,bytearray([0]))
#     result = dev.readfrom(address,2)
#     config = read_config()
#     #print('read config during reading::', bin(config))
#     # config &= ~(7<<12) & ~(7<<9)
#     # config |= (4<<12) | (1<<9) | (1<<15)
#     # config = [int(config >> i & 0xFF) for i in (8,0)]
#     # print('after read modifcation: ',config)
#     # dev.writeto(address,bytearray([1]+config))
#     set_config(channel)
#     return result[0] << 8 | result[1]


def val_to_voltage(val,max_val=26100,voltage_ref=3.3):
    return val / max_val * voltage_ref

# set_config('111')
# while True:
#     #print('check bit 15')
#     rbit = (read_config()>>15)&1
#     if rbit:
#         break
#print('before main loop config read: ', bin(read_config()))




# noinspection PyArgumentList
uart0 = UART(0,
             baudrate=9600,
             tx=Pin(0),
             rx=Pin(1))

print("Sending Messages on Serial port")
internal_led = Pin(25, Pin.OUT)

uart0.write(GeneralEncoder('pico_join', 'Sending data every 2 seconds').message)
irig = Irrigator(PumpStateMachine(), ReservoirStateMachine())


def on_command_completion(command):
    print(f"Command completed: {command.action}. Result: {command.result}")

ads_adc = ADS1115(72)
# def read_adc_from_channel(ads,channel):
#
#     ads.set_config(channel)
#     while True:
#         rbit = (ads.read_config() >> 15) & 1
#         if rbit:
#             break
#     # time.sleep(0.01)
#     adc_val = ads.read_value(channel)
#     return adc_val


while True:

    print('main loop start')
    start_time = time.ticks_ms()

    volts = ads_adc.val_to_voltage(ads_adc.read_adc_from_channel('111'))    # adc channel "4" - > A3
    sensor.measure()  # Recovers measurements from the DHT-22 sensor
    photo = adc.read_u16()  # Photoresistor
    light = round((1 - photo / 65535) * 100, 2)  # convert photo re

    volts2 = ads_adc.val_to_voltage(ads_adc.read_adc_from_channel('111'))  # adc channel 1 -> A0

    sensor_packet_dict = {'temp': sensor.temperature(),
                          'humidity': sensor.humidity(),
                          'light': light,
                          'voltage': volts,
                          'voltage2': volts2
                          }
    uart0.write(SensorEncoder(sensor_packet_dict).message)

    weight = irig.reservoir.weight
    print(f"Current reservoir weight: {irig.reservoir.weight}g, target = {irig.target_weight}g")

    if uart0.any():
        print('uart available')
        b = uart0.readline()
        msg = b.decode('utf-8')
        print(msg)
        if msg.strip() == 'bb':
            print('add command')
            new = DeviceCommand('water', target=4, on_completion=on_command_completion)
            irig.enqueue_command(new)

    irig.tick()
    internal_led.toggle()

    end_time = time.ticks_ms()

    print(f"total time taken this tick: {(time.ticks_diff(end_time, start_time))}ms")
    print('main loop end')
    time.sleep(2)
    print()

