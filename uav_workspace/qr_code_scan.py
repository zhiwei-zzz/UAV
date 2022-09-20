# -*- coding: utf-8 -*-

import cv2
import time
from connect_uav import UPUavControl
from pyzbar import pyzbar

from multiprocessing import Process
from multiprocessing.managers import BaseManager
import numpy as np

cap = cv2.VideoCapture(0)
ret = cap.set(3, 640)  # 设置帧宽
ret = cap.set(4, 480)  # 设置帧高


class QrCodeScan():
    def __init__(self):

        # 二维码信息
        self.scan_content = ""
        # 是否开始执行
        self.isStart = False
        # 是否前进
        self.isForward = False
        # 是否完成右转
        self.isTurnRight = False
        # 是否执行降落
        self.isLanded = False
        # 转向计数
        self.trun_time = 0

        # 实例化进程间无人机控制实例
        BaseManager.register('UPUavControl', UPUavControl)
        manager = BaseManager()
        manager.start()
        self.airplanceApi = manager.UPUavControl()
        controllerAir = Process(name="controller_air", target=self.api_init)
        controllerAir.start()
        time.sleep(0.5)
        # 打开摄像头进行识别
        self.start_video()



    def api_init(self):
        print("process start")
        # 控制舵机转动到0度角
        time.sleep(0.5)
        self.airplanceApi.setServoPosition(90)

    def start_video(self):
        while cap.isOpened():
            ret, frame = cap.read()
            src = frame.copy()
            result = frame.copy()

            # 找到图像中的条形码并进行解码
            barcodes = pyzbar.decode(result)
            # 循环检测到的条形码
            for barcode in barcodes:
                # 提取条形码的边界框的位置
                # 画出图像中条形码的边界框
                (x, y, w, h) = barcode.rect
                cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 5)
                # 条形码数据为字节对象，所以如果我们想在输出图像上
                # 画出来，就需要先将它转换成字符串
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type
                # 绘出图像上条形码的数据和条形码类型
                text = "{}".format(barcodeData, barcodeType)
                self.scan_content = barcodeData
                # 将识别到的二维码框到图像上
                cv2.putText(result, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 0, 0), 2)

                points = barcode.polygon
                # print(points)
                p1_x = points[0].x
                p2_x = points[1].x
                p3_x = points[2].x
                p4_x = points[3].x

                p1_y = points[0].y
                p2_y = points[1].y
                p3_y = points[2].y
                p4_y = points[3].y

                # 定义四个顶点坐标
                pts = np.array([[p1_x, p1_y], [p2_x, p2_y], [p3_x, p3_y], [p4_x, p4_y]], np.int32)
                # 顶点个数：4，矩阵变成4*1*2维
                pts = pts.reshape((-1, 1, 2))

                cv2.polylines(result,[pts],True,(0, 255, 0))

                # cv2.circle(result, (p1_x, p1_y), 5, (0, 0, 255), -1)
                # cv2.circle(result, (p2_x, p2_y), 5, (0, 255, 0), -1)
                cv2.circle(result, (p3_x, p3_y), 5, (0, 0, 255), -1)
                # print(points)
                # print(str(p1_y)+"      "+str(p2_y))
                if self.scan_content == "forward":
                    self.isForward = True
#                     if p1_y - p4_y > 20 and p2_y - p3_y > 30:
#                         if abs(p3_y - p4_y) > 20:
#                             print("turn_right")
#                             self.isForward = False
#                             self.airplanceApi.turn_right(130)
#                         else:
#                             self.isForward = True
#                     elif p2_y - p1_y > 20 and p3_y - p4_y > 30:
#                         if abs(p1_y - p4_y) > 20:
#                             self.isForward = False 
#                             print("turn_left")
#                             self.airplanceApi.turn_left(130)
#                         else:
#                             self.isForward = True
#                             self.scan_content = ""


                if self.isForward:
                    print("forward")
                    self.airplanceApi.move_forward(160)

                if self.scan_content == "right":
                    self.airplanceApi.move_right(160)
                    
#                     self.trun_time += 1
#                     self.isForward = False
#                     if self.trun_time > 20:
#                         if p1_y - p4_y > 20 and p2_y - p3_y > 30:
#                             if abs(p3_y - p4_y) > 20:
#                                 print("turn_right")
#                                 self.airplanceApi.turn_right(130)
#                             else:
#                                 self.isForward = True
#                                 self.isTurnRight = True
#                                 self.scan_content = ""
#                         elif p2_y - p1_y > 20 and p3_y - p4_y > 30:
#                             if abs(p1_y - p4_y) > 20:
#                                 print("turn_left")
#                                 self.airplanceApi.turn_left(130)
#                             else:
#                                 self.isForward = True
#                                 self.isTurnRight = True
#                                 self.scan_content = ""
#                     else:
#                         print("turn_right")
#                         self.airplanceApi.turn_right(130)


            # 判断是否降落状态，二维码信息是否是landed,避免多次调用降落函数
            if self.isLanded == False and self.scan_content == "landed":
                print("landed")
                self.airplanceApi.land()
                self.isForward = False
                self.isLanded = True


            # 显示二维码识别结果
            cv2.imshow("result",result)
            cv2.imshow("src",src)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    qr_code_scan = QrCodeScan()
