# Wasabot - "Sender"


See "Wasabot - Server". This is a client based on RPi Pico using Micropython

## Phase 1
I will log sensor them in a database, and also provide a web ui to display them.

### So far I have:
* Designed a simple serial messaging protocol
* Implemented a testing environment
* Set up a raspberry pi pico to send data from a DHT-22 sensor
* Added photo resistor to sensor data

## Phase 2
Will set up various thresholds and logic to detect if environmental conditions are suitable, and actuate things to get
things in order

## So far I have:
* Implemented multi channel ADC (ads1115) over I2C
* State Machines
* Water pump
* Pico can receive commands but have not updated rpi
* Investigating Pico W and rest api to replace serial comms


### Outstanding for Phase 2
* Receive Commands from server and report result
* Soil moisture sensor - hardware tested
* Fan
* Reservoir Temperature Sensor
* Investigate alternative to rest api for rapid reporting
* Add various sensor regimes (eg. demo, ads1115 vs onboard vs hd711)
* Add different targets for state machines (time, weight)
* Investigate connecting sensors over rj45 


## Known Issues

If the checksum evaluates to "\n" this will add a line break. Ironically found this out with message: "data:hello world".

Probably need to figure out how to handle that, or change the checksum method.
