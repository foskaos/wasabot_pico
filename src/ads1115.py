from machine import Pin, I2C


class ADS1115:

    def __init__(self,address):
        self.address = address
        self.dev = I2C(1, freq=400000, scl=Pin(15), sda=Pin(14))
        devices = self.dev.scan()
        for device in devices:
            print(devices)

        self.set_config('111')
        self.check_ready()

    @staticmethod
    def create_config_string(mux):
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

        adc_val = self.read_value(channel)
        return adc_val

    @staticmethod
    def val_to_voltage(val, max_val=26100, voltage_ref=3.3):
        return val / max_val * voltage_ref


