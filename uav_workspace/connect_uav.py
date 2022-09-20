import time
from serial_helper import SerialHelper
from pid_t import PID_t
import threading


class UPUavControl():
    
    def __init__(self):
        # 创建串口对象
        self.ser = SerialHelper()
        self.ser.on_connected_changed(self.myserial_on_connected_changed)

        # 发送的数据队列
        self.msg_list = []
        # 是否连接成功
        self._isConn = False
        # 是否在飞行阶段
        self.isFly = False
        # 一键起飞定高的高度值，单位cm
        self.settingHeight = 0

        # pid 初始化对象
        self.pid = PID_t()
        # 飞机油门杆量死区
        self.dead_area = 50
        # 飞机最小上升杆量
        self.min_up = 53
        # 飞机最小下降杆量
        self.min_down = 47
        # 当前高度
        self.current_height = 0

        # 通信线程创建启动
        sendThread = threading.Thread(name = "send_thread",target=self.send_msg)
        sendThread.setDaemon(True)
        sendThread.start()

    # 串口连接状态回调函数
    def myserial_on_connected_changed(self, is_connected):
        if is_connected:
            print("Connected")
            self._isConn = True
            self.ser.connect()
            self.ser.on_data_received(self.on_data_received)
        else:
            print("DisConnected")

    # 串口通信发送
    def write(self, data):
        self.ser.write(data, True)

    # 串口通信线程发送函数
    def send_msg(self):
        while True:
            if len(self.msg_list) > 0 and self._isConn:
                self.ser.write(self.msg_list[0])
                self.msg_list.remove(self.msg_list[0])

    # 串口数据包构建方法
    def generateCmd(self, device, cmd, len, data):
        buffer = [0] * (len + 6)
        buffer[0] = 0xF5
        buffer[1] = 0x5F
        buffer[2] = device & 0xFF
        buffer[3] = cmd & 0xFF
        buffer[4] = len & 0xFF
        for i in range(len):
            buffer[5 + i] = data[i]

        check = 0
        for i in range(len + 3):
            check += buffer[i + 2]

        buffer[len + 5] = (~check) & 0xFF
        return buffer, len+6

    # 无人机移动函数封装
    def setMoveAction(self, y, x, z, yaw):
        data = [0] * 8
        data[0] = y & 0xFF
        data[1] = (y >> 8) & 0xFF
                    
        data[2] = x & 0xFF
        data[3] = (x >> 8) & 0xFF
                   
        data[4] = z & 0xFF
        data[5] = (z >> 8) & 0xFF
            
        data[6] = yaw & 0xFF
        data[7] = (yaw >> 8) & 0xFF

        buffer,len = self.generateCmd(0x55, 0x01, 0x08, data)
        self.msg_list.append(buffer)

    # 返回无人机当前高度值
    def get_current_height(self):
        return self.current_height

    # 控制云台舵机运动角度，角度区间0-90
    def setServoPosition(self,angel):
        data = [0] * 2
        data[0] = angel & 0xFF
        data[1] = (angel >> 8) & 0xFF
        buffer,len = self.generateCmd(0x55, 0x03, 0x02, data)
        self.msg_list.append(buffer)

    # 控制无人机向前飞行
    def move_forward(self, speed):
        self.setMoveAction(0, speed, 0, 0)

    # 控制无人机向后飞行
    def move_backward(self, speed):
        self.setMoveAction(0, -speed, 0, 0)

    # 控制无人机向左飞行
    def move_left(self, speed):
        self.setMoveAction(-speed, 0, 0, 0)

    # 控制无人机向右飞行
    def move_right(self, speed):
        self.setMoveAction(speed, 0, 0, 0)

    # 控制无人机向上飞行
    def move_up(self, speed):
        self.setMoveAction(0, 0, speed, 0)

    # 控制无人机向下飞行
    def move_down(self, speed):
        self.setMoveAction(0, 0, speed, 0)

    # 控制无人机向左转向
    def turn_left(self, speed):
        self.setMoveAction(0, 0, 0, -speed)

    # 控制无人机向右转向
    def turn_right(self, speed):
        self.setMoveAction(0, 0, 0, speed)

    # 控制无人机解锁
    def unclock(self):
        self.setMoveAction(-500, -500, -500, 500)

    # 控制无人机停止运行
    def stop(self):
        self.setMoveAction(0, 0, 0, 0)
        self.setMoveAction(0, 0, -500, 0)
        
    
    def onekey_takeoff(self,height):
        data = [0] * 1
        data[0] = height & 0xFF
        buffer,len = self.generateCmd(0x55, 0x05, 0x01, data)
        self.msg_list.append(buffer)

    # 控制无人机降落
    def land(self):
        self.isFly = False
        buffer = [0] * 6
        buffer[0] = 0xF5
        buffer[1] = 0x5F
        buffer[2] = 0x55
        buffer[3] = 0x06
        buffer[4] = 0
        buffer[5] = 0xA4
        self.msg_list.append(buffer)
        self.msg_list.append(buffer)

    # 获取无人机高度值线程启动
    def get_air_height(self):
        self.getHeightThread = threading.Thread(target=self.on_height_callback, name="get_height")
        self.getHeightThread.setDaemon(True)
        self.getHeightThread.start()

    # 设置无人机悬停起飞高度，单位cm
    def set_height(self,height):
        self.settingHeight = height
        self.isFly = True

    # 获取无人机高度值函数，循环执行
    def on_height_callback(self):
        while True:
            if self._isConn and self.isFly:
                buffer = [0] * 6
                buffer[0] = 0xF5
                buffer[1] = 0x5F
                buffer[2] = 0x55
                buffer[3] = 0x02
                buffer[4] = 0
                buffer[5] = 0xA8
                self.msg_list.append(buffer)
                time.sleep(0.01)
                
    # 无人机数据包读取回调函数
    def on_data_received(self, data):
        if data[2] == 0x55 and data[3] == 0x06:
            state = data[5]
            print(state)
        
        # 获取无人机高度值
        if data[2] == 0x55 and data[3] == 0x02 and self.settingHeight != 0:
            height = ((data[5] & 0xFF) | ((data[6] & 0xFF) << 8) | ((data[7] & 0xFF) << 16) | ((data[8] & 0xFF) << 24))
            self.current_height = height
            if height <= 30:
                height = 0
            # 通过pid算法计算悬停定高的油门杆量值
            speed = round(self.pid.pid_calculate(0.001,0,self.settingHeight,height))
            # 判断计算杆量值死区
            if 0 < speed < self.dead_area:
                speed = speed + (self.min_up - speed)
            if -self.dead_area < speed < 0:
                speed = speed - (self.min_down - speed)

            # 判断是否在设定高度，误差正负 3cm
            if abs(height - self.settingHeight) < 3:
                self.move_up(0)
                self.move_down(0)
            else:
                if height - self.settingHeight < 0:
                    self.move_up(speed)
                elif height - self.settingHeight > 0:
                    self.move_down(speed)
            
            print("height: " + str(height) + "  speed: " + str(speed))

if __name__ == '__main__':
    connect = UPUavControl()
    time.sleep(1)
#     connect.stop()
#     connect.unclock()
#     connect.land()
    connect.get_air_height()
    connect.set_height(70)


        
        


