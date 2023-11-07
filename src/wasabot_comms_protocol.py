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


class DecodedMessage:
    def __init__(self, message_type: str, payload: [str]):
        self.message_type = message_type
        self.payload = payload

    def __str__(self):
        return f"Type: {self.message_type}, Payload: {self.payload}"


class MessageDecoder:
    def __init__(self):
        # Initialize any necessary state or settings for decoding
        ...
    def decode(self, serial_data):
        try:
            # Implement your decoding logic here, e.g., parsing JSON
            decoded_data = self._parse_serial_line(serial_data)
            return decoded_data
        except Exception as e:
            print("Error decoding data:", e)

            return None

    @staticmethod
    def calculate_checksum(data):
        checksum = 0
        for byte in data:
            checksum ^= byte
        return bytes([checksum])

    def _parse_serial_line(self,ln):
        line = ln.strip()
        if line:
            if (line[0] == 60) and line[-1] == 62:
                # we are in this block because the start and end chars were detected,
                # so we can extract the body from the line
                msg = line[1:-1]
                r_ck = msg[len(msg) - 1:]
                data = msg[:len(msg) - 1]

                # compare received checksum with calculated one
                if r_ck == self.calculate_checksum(data):
                    # convert data bytes to string
                    string_rep = data.decode('utf-8')
                    # data body is delimited with ":" character
                    msg_parts = string_rep.split(":")
                    # take the first value as which client sent the message, put the rest in
                    msg_type, *body = msg_parts
                    # print(f'from: {msg_from}, body: {body}')
                    message = DecodedMessage(msg_type,body)
                    return message
                else:
                    # checksum didn't work, so message bad

                    raise ValueError("Checksum Failed")
            else:
                print('invalid message: ', line)
                raise ValueError("Start/Stop Characters not found")