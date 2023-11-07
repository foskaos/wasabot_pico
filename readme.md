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
* 

### Outstanding for Phase 2
* Receive Commands from server and report result
* State Machines
* Water pump
* Soil moisture sensor
* Fan
* Reservoir Temperature Sensor


## Known Issues

If the checksum evaluates to "\n" this will add a line break. Ironically found this out with message: "data:hello world".

Probably need to figure out how to handle that, or change the checksum method.
