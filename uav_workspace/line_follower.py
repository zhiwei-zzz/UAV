# -*- coding: utf-8 -*-

import numpy as np
import cv2
import time
import math

from pyzbar import pyzbar
from connect_uav import UPUavControl
from multiprocessing import Process
from multiprocessing.managers import BaseManager

red_lower = np.array([0,43,46])
red_upper = np.array([10,255,255])

red_lower1 = np.array([156,43,46])
red_upper1 = np.array([180,255,255])

kernel = np.ones((5, 5), np.uint8)  # 卷积核
font = cv2.FONT_HERSHEY_SIMPLEX
red_min = np.array([20, 100, 100])
red_max = np.array([5, 255, 255])
red2_min = np.array([156, 128, 46])
red2_max = np.array([180, 255, 255])

cap = cv2.VideoCapture(0)
no_slice = 4

center = (240, 227)

class LineFollower():
    def __init__(self):

        #二维码信息
        self.scan_content = ""
        #二维码是否在中心位置
        self.is_code_center = False
        #是否继续巡线
        self.is_follow = True
        #是否沿直线行驶
        self.is_forward = False
        #是否有左右偏差
        self.is_offset = False

        #实例化进程间无人机控制实例
        BaseManager.register('UPUavControl',UPUavControl)
        manager = BaseManager()
        manager.start()
        self.airplanceApi = manager.UPUavControl()
        controllerAir = Process(name = "controller_air",target=self.api_init)
        controllerAir.start()

        # 控制无人机到指定高度，并且悬停5秒
        time.sleep(1)
        self.airplanceApi.onekey_takeoff(60)
#         self.airplanceApi.set_height(60)
#         self.airplanceApi.get_air_height()
        time.sleep(5)
        #打开摄像头进行识别
        self.start_video()
        super(LineFollower, self).__init__()
        
    def api_init(self):
        print("process start")
        time.sleep(0.5)
        #控制舵机旋转90度
        self.airplanceApi.setServoPosition(90)


    #摄像头识别开始
    def start_video(self):
        while cap.isOpened():
            ret,frame = cap.read()
            frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
            
            #红色圆点识别
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(hsv, red_lower, red_upper)
            mask2 = cv2.inRange(hsv, red_lower1, red_upper1)
            mask = mask1 + mask2
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)
            red_img = cv2.GaussianBlur(frame, (5, 5), 0)
            hsv = cv2.cvtColor(red_img, cv2.COLOR_BGR2HSV)
            res = cv2.bitwise_and(red_img, red_img, mask=mask)
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]




            #判断是否沿直线走
            if self.is_forward:
                self.airplanceApi.move_forward(200)

            # 识别到红色圆点
            if  len(cnts) > 0 and self.is_forward ==False:
#                 x, y, radius = circles[0][0]
#                 c = (x, y)
#                 cv2.circle(frame, c, radius, (0, 255, 0), 2)
                cnt = max(cnts, key=cv2.contourArea)
                (x, y), radius = cv2.minEnclosingCircle(cnt)
                cv2.circle(red_img, (int(x), int(y)), int(radius), (0, 250, 0), -1)
                self.is_follow = False
                offset_x = (x + radius) - 240

                #计算偏移量
                if 20 < offset_x :
                    print("move left")
                    self.airplanceApi.move_left(150)
                elif offset_x < -20 :
                    print("move right")
                    self.airplanceApi.move_right(150)
                else:
                    self.is_forward = True
                print("红色识别成功")


            #二维码识别
            self.decode(frame)
            if frame is not None:
                #判断二维码信息,如果二维码信息为landed并且在中心上执行降落
                if self.scan_content == "landed" and self.is_code_center:
                    self.is_follow = False
                    self.is_forward = False
                    self.airplanceApi.land()

                #黑线识别
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                img = self.remove_background(img, True)
                slices, cont_cent = self.slice_out(img, no_slice)
                img = self.repack(slices)
                self.line(img, center, cont_cent)

                # 显示图片三个识别窗口
                cv2.imshow('frame', img)
                cv2.imshow('scan', frame)
                # cv2.imshow("res", res)
            else:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


    #二维码识别
    def decode(self,image):
        # 找到图像中的条形码并进行解码
        barcodes = pyzbar.decode(image)
        # 循环检测到的条形码
        for barcode in barcodes:
            # 提取条形码的边界框的位置
            # 画出图像中条形码的边界框
            (x, y, w, h) = barcode.rect
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 5)
            # 条形码数据为字节对象，所以如果我们想在输出图像上
            # 画出来，就需要先将它转换成字符串
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
            # 绘出图像上条形码的数据和条形码类型
            text = "{}".format(barcodeData, barcodeType)
            self.scan_content = barcodeData
            cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 0, 0), 2)
            
            offset_x = (x + w) / 2
            offset_y = (x + h) / 2

            #计算二维码偏移量调节飞机对准二维码
            if offset_y < 217:
                self.airplanceApi.move_left(150)
                self.is_code_center = False
            elif offset_y > 237:
                self.airplanceApi.move_right(150)
                self.is_code_center = False
            elif offset_x < 225:
                self.airplanceApi.move_left(150)
                self.is_code_center = False
            elif offset_x > 255:
                self.airplanceApi.move_right(150)
                self.is_code_center = False
            else:
                self.is_code_center = True
            print(text)

    # 获取中心点
    def get_contour_center(self,contour):
        m = cv2.moments(contour)
        if m["m00"] == 0:
            return [0, 0]
        x = int(m["m10"] / m["m00"])
        y = int(m["m01"] / m["m00"])
        return [x, y]

    def process(self,image):
        _, thresh = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY_INV)  # Get Threshold
        contours,hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # Get contouro
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            cv2.drawContours(image, [main_contour], -1, (150, 150, 150), 2)
            contour_center = self.get_contour_center(main_contour)
            cv2.circle(image, tuple(contour_center), 2, (150, 150, 150), 2)
        else:
            return image,(0,0)
        return image, contour_center

    def slice_out(self,im, num):
        cont_cent = list()

        height, width = im.shape[:2]
        sl = int(height / num)
        sliced_imgs = list()
        for i in range(num):
            part = sl * i
            crop_img = im[part:part + sl, 0:width]
            processed = self.process(crop_img)
            sliced_imgs.append(processed[0])
            cont_cent.append(processed[1])
        return sliced_imgs, cont_cent

    def remove_background(self,image, b):
        up = 100
        lo = 0
        # create NumPy arrays from the boundaries
        lower = np.array([lo], dtype="uint8")
        upper = np.array([up], dtype="uint8")
        # ----------------COLOR SELECTION-------------- (Remove any area that is whiter than 'upper')
        if b is True:
            mask = cv2.inRange(image, lower, upper)
            image = cv2.bitwise_and(image, image, mask=mask)
            image = cv2.bitwise_not(image, image, mask=mask)
            image = (255 - image)
            return image
        else:
            return image

    def repack(self,images):
        im = images[0]
        for i in range(len(images)):
            if i == 0:
                im = np.concatenate((im, images[1]), axis=0)
            if i > 1:
                im = np.concatenate((im, images[i]), axis=0)
        return im

    def line(self,image, center, cont_cent):
        # 把图像上下4等分划线
        cv2.line(image, (0, 65), (480, 65), (30, 30, 30), 1)
        cv2.line(image, (0, 130), (480, 130), (30, 30, 30), 1)
        cv2.line(image, (0, 195), (480, 195), (30, 30, 30), 1)
        cv2.line(image, (240, 0), (240, 260), (30, 30, 30), 1)

        #计算每个块中心点间的偏移角度
        line_angle1 = math.atan2(cont_cent[1][0] - cont_cent[0][0], cont_cent[1][1] + 65 - cont_cent[0][1])
        line_angle1 = int(180 * line_angle1 / math.pi)

        line_angle2 = math.atan2(cont_cent[2][0] - cont_cent[1][0], cont_cent[2][1] + 65 * 2 - cont_cent[1][1] + 65)
        line_angle2 = int(180 * line_angle2 / math.pi)

        line_angle3 = math.atan2(cont_cent[3][0] - cont_cent[2][0], cont_cent[3][1] + 65 * 3 - cont_cent[2][1] + 65 * 2)
        line_angle3 = int(180 * line_angle3 / math.pi)
        #计算各点的x轴的偏移量
        offset_x1 = cont_cent[1][0] - cont_cent[0][0]
        offset_x2 = cont_cent[2][0] - cont_cent[1][0]
        offset_x3 = cont_cent[3][0] - cont_cent[2][0]
        #计算第三个点与中心点的偏移量
        offset_center = cont_cent[2][0] - 240
        # print("角度1：" + str(line_angle1) + "  角度2：" + str(line_angle2) + "  角度3：" + str(line_angle3))
        for i in range(len(cont_cent)):
            cv2.line(image, center, (cont_cent[i][0], cont_cent[i][1] + 65 * i), (100, 100, 100), 1)
        #判断是否在巡线，判断下一步的飞行姿态
        if self.is_follow:
            if offset_center > 70:
                self.airplanceApi.move_right(150)
                print("move_right")
            elif offset_center < -70:
                self.airplanceApi.move_left(150)
                print("move_left")
            else:
                self.airplanceApi.move_forward(150)

                if abs(line_angle1) > 15 or abs(line_angle2) > 15 or abs(line_angle3) > 15:
                    if cont_cent[0][0] != 0 and cont_cent[1][0] != 0:
                        if offset_x1 > 0:
                            print("turn_left")
                            self.airplanceApi.turn_left(120)
                        else:
                            print("turn_right")
                            self.airplanceApi.turn_right(120)
                    else:
                        if cont_cent[1][0] != 0 and cont_cent[2][0] != 0:
                            if offset_x2 > 0:
                                print("turn_left")
                                self.airplanceApi.turn_left(120)
                            else:
                                print("turn_right")
                                self.airplanceApi.turn_right(120)
                        else:
                            if cont_cent[2][0] != 0 and cont_cent[3][0] != 0:
                                if offset_x3 > 0:
                                    print("turn_left")
                                    self.airplanceApi.turn_left(120)
                                else:
                                    print("turn_right")
                                    self.airplanceApi.turn_right(120)

if __name__ == '__main__':
    line_follower = LineFollower()
