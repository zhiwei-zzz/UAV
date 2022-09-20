
import time
import serial

class Test():
    
    def __init__(self, Port="/dev/ttyUSB0", BaudRate="115200", ByteSize="8", Parity="N", Stopbits="1"):

        self.port = Port
        self.baudrate = BaudRate
        self.bytesize = ByteSize
        self.parity = Parity
        self.stopbits = Stopbits
        self.threshold_value = 1
        self.receive_data = ""

        self._serial = None
        self._is_connected = False

    def connect(self, timeout=2):

        self._serial = serial.Serial()
        self._serial.port = self.port
        self._serial.baudrate = self.baudrate
        self._serial.bytesize = int(self.bytesize)
        self._serial.parity = self.parity
        self._serial.stopbits = int(self.stopbits)
        self._serial.timeout = timeout

        try:
            self._serial.open()
            if self._serial.isOpen():
                self._is_connected = True
                print("connect success")
        except Exception as e:
            self._is_connected = False
    
    def write(self, data, isHex=False):

        if self._is_connected:
            print("send data")
            self._serial.write(data)
        else:
            print("port no open")

    
if __name__ == '__main__':
    
    
    t = Test()
    t.connect();
    buffer = [0] * 6
    buffer[0] = 0xF5
    buffer[1] = 0x5F
    buffer[2] = 0x55
    buffer[3] = 0x0A
    buffer[4] = 0x00
    buffer[5] = 0xA0
    
    send_count = 0
    time.sleep(1)
    while True:
        t.write(buffer)
        time.sleep(1)
#         send_count += 1
#         if send_count >= 60:
#             break;


