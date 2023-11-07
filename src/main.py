from machine import UART, Pin, ADC, I2C
import time
import dht

from states_mach import PumpState,PumpStateMachine,ReservoirState,ReservoirStateMachine,Irrigator,DeviceCommand,CommandStatus
from wasabot_comms_protocol import MessageEncoder, SensorEncoder,CommandEncoder,GeneralEncoder,DataEncoder
from ads1115 import ADS1115

dht_pin = 2
sensor = dht.DHT22(Pin(dht_pin))
adc = ADC(Pin(26))

uart0 = UART(0,9600)

print("Sending Messages on Serial port")
internal_led = Pin(25, Pin.OUT)

uart0.write(GeneralEncoder('pico_join', 'Sending data every 2 seconds').message)
irig = Irrigator(PumpStateMachine(), ReservoirStateMachine())


def on_command_completion(command):
    print(f"Command completed: {command.action}. Result: {command.result}")


ads_adc = ADS1115(72)

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

