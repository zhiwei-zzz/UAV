# -*- coding: utf-8 -*-

import numpy as np
import cv2
import time
from connect_uav import UPUavControl
from multiprocessing import Process
from multiprocessing.managers import BaseManager

red_min = np.array([0, 128, 46])
red_max = np.array([5, 255, 255])
red2_min = np.array([156, 128, 46])
red2_max = np.array([180, 255, 255])
cap = cv2.VideoCapture(0)
cv2.resizeWindow("resized", 640, 480)
ret = cap.set(3, 640)  # 设置帧宽
ret = cap.set(4, 480)  # 设置帧高
font = cv2.FONT_HERSHEY_SIMPLEX  # 设置字体样式
kernel = np.ones((5, 5), np.uint8)  # 卷积核

class RedFollower():

    def __init__(self):

        # 实例化进程间无人机控制实例
        BaseManager.register('UPUavControl', UPUavControl)
        manager = BaseManager()
        manager.start()
        self.airplanceApi = manager.UPUavControl()
        controllerAir = Process(name="controller_air", target=self.api_init)
        controllerAir.start()
        time.sleep(0.5)
        self.start_video()

    def api_init(self):
        print("process start")
        time.sleep(1)
        #控制舵机旋转90度
        self.airplanceApi.setServoPosition(0)
    
    def start_video(self):
        while cap.isOpened():
            r, frame = cap.read()
            src = frame.copy()
            hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
            res = src.copy()
            result = src.copy()
            mask_red1 = cv2.inRange(hsv, red_min, red_max)
            mask_red2 = cv2.inRange(hsv, red2_min, red2_max)
            mask = cv2.bitwise_or(mask_red1, mask_red2)
            res = cv2.bitwise_and(src, src, mask=mask)
            h, w = res.shape[:2]
            blured = cv2.blur(res, (5, 5))
            ret, bright = cv2.threshold(blured,10,255,cv2.THRESH_BINARY)
            gray = cv2.cvtColor(bright,cv2.COLOR_BGR2GRAY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
            contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:

                largest_area = 0
                choose = 0
                target_contour = None
                for i in range(0, len(contours)):
                    x, y, w, h = cv2.boundingRect(contours[i])
                    area = w*h
                    if area > largest_area:
                        largest_area = area
                        choose = i
                target_contour = contours[choose]
                if target_contour is not None:
                    tx, ty, tw, th = cv2.boundingRect(target_contour)
                    txmin = max(0, tx-20)
                    tymin = max(0, ty-20)
                    txmax = min(640, tx+tw+20)
                    tymax = min(480, ty+th+20)

                    ###get roi area###
                    red_roi = src[tymin: tymax, txmin: txmax]
                    gray_roi = closed[tymin: tymax, txmin: txmax]
                    circles = cv2.HoughCircles(gray_roi, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=20, minRadius=0, maxRadius=0)
                    if circles is not None:
                        circles = np.uint16(np.around(circles))
                        for i in circles[0, :]:
                            cv2.circle(src, (i[0], i[1]), i[2], (0, 0, 255), 2)
                            cv2.circle(src, (i[0], i[1]), 2, (255, 0, 0), 2)
                        if len(circles) == 1:
                            target_circle = circles[0]
                            ###calc offset x###
                            offset_x = target_circle[0][0] + txmin - 320 ###offset x to center
                            offset_y = target_circle[0][1] + tymin - 240 ###offset y to center
                            if offset_x < -30:
                                self.airplanceApi.move_left(200)
                                print("move left")
                            elif offset_x > 30:

                                self.airplanceApi.move_right(200)
                                print("move right")

                        cv2.imshow("ROI", red_roi)
            cv2.imshow("src", frame)
            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break
        cap.release()
        cv2.destroyAllWindows()
if __name__ == '__main__':
    red_follower = RedFollower()
     
    
    

