from machine import UART, Pin, ADC, I2C
import time
import dht
from states_mach import PumpStateMachine,ReservoirStateMachine,Irrigator,DeviceCommand
from wasabot_comms_protocol import MessageEncoder, SensorEncoder,CommandEncoder,GeneralEncoder,DataEncoder
from ads1115 import ADS1115, ResADC

dht_pin = 2
sensor = dht.DHT22(Pin(dht_pin))
adc = ADC(Pin(26))

uart0 = UART(0,9600,timeout=500)

print("Sending Messages on Serial port")
internal_led = Pin(25, Pin.OUT)
ads_adc = ADS1115(72)

# res_adc = ResADC()
uart0.write(GeneralEncoder('pico_join', 'Sending data every 2 seconds').message)
# irig = Irrigator(PumpStateMachine(), ReservoirStateMachine(res_adc))


def on_command_completion(command):
    print(f"Command completed: {command.action}. Result: {command.result}")


def on_command_failed(command):
    print(f"Command failed: {command.action}. Result: {command.result}")


def read_dht():
    retry_counter = 0
    while True:
        try:
            sensor.measure()
            time.sleep(0.1)
            t = sensor.temperature()
            h = sensor.humidity()
            if retry_counter > 0:
                print(f'dht ok after {retry_counter} tries')
            break
        except:
            retry_counter += 1
            print(f'dht reading failed attempt {retry_counter}, try again')
            time.sleep(0.1)

    return t, h


last_temp, last_humidity = read_dht()
time.sleep(2)

while True:

    print('main loop start')
    start_time = time.ticks_ms()

    #volts = ads_adc.val_to_voltage(ads_adc.read_adc_from_channel('100'))    # adc channel "4" - > A3
    # Recovers measurements from the DHT-22 sensor
    photo = ads_adc.read_adc_from_channel('100') #adc.read_u16()  # Photoresistor
    light = round((1 - photo / 26100) * 100, 2)  # convert photo re

    # volts2 = ads_adc.val_to_voltage(ads_adc.read_adc_from_channel('111'))  # adc channel 1 -> A0

    # rw = res_adc.get_res_weight()

    #print(f'photo adc: {photo}')

    # r_weight = irig.reservoir.weight
    # print(f"Current reservoir weight: {irig.reservoir.weight}g, target = {irig.target_weight}g")
    try:
        temp, humidity = read_dht()
    except:
        temp = last_temp
        humidity = last_humidity
        # 'voltage': round(volts, 2),
    last_temp = temp
    last_humidity = humidity

    sensor_packet_dict = {'temp': temp,
                          'humidity': humidity,
                          'light': light,
                          # 'reservoir_weight': round(r_weight, 2)
                          }

    uart0.write(SensorEncoder(sensor_packet_dict).message)


    if uart0.any():
        print('uart available')
        b = uart0.readline()
        msg = b.decode('utf-8')
        print(msg)
        if msg.strip() == 'bb':
            print('add command')
            # new = DeviceCommand('water', target=4, on_completion=on_command_completion, on_failure=on_command_failed)
            # irig.enqueue_command(new)

    # irig.tick()
    internal_led.toggle()

    end_time = time.ticks_ms()

    print(f"total time taken this tick: {(time.ticks_diff(end_time, start_time))}ms")
    print('main loop end')
    time.sleep(2)
    print()

