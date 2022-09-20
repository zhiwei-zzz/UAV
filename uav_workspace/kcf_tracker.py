# -*- coding: utf-8 -*-

import cv2
import time
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
from video_capture import VideoCapture
from connect_uav import UPUavControl
from multiprocessing import Process
from multiprocessing.managers import BaseManager

class KCFTracker(VideoCapture):
    def __init__(self):
        self.kcf_tracker = None
        # 实例化进程间无人机控制实例
        BaseManager.register('UPUavControl', UPUavControl)
        manager = BaseManager()
        manager.start()
        self.airplanceApi = manager.UPUavControl()
        controllerAir = Process(name="controller_air", target=self.api_init)
        controllerAir.start()
        time.sleep(0.5)
        # 控制云台旋转到0度
        self.airplanceApi.setServoPosition(0)
        self.initKCF()
        super(KCFTracker, self).__init__()


    def api_init(self):
        print("process start")

    def initKCF(self):

        self.kcf_tracker = cv2.TrackerKCF_create()

    def process_image(self, image):
        try:
            if self.detect_box is None:
                return image
            src = image.copy()
            if self.track_box is None or not self.is_rect_nonzero(self.track_box):
                self.track_box = self.detect_box
                if self.kcf_tracker is None:
                    raise Exception("tracker not init")
                status = self.kcf_tracker.init(src, self.track_box)
                if not status:
                    raise Exception("tracker initial failed")
            else:
                self.track_box = self.track(src)
                if self.track_box is not None:
                    (tx, ty, tw, th) = self.track_box
                    target_track_x = tx + tw / 2
                    target_track_y = ty + th / 2
                    offset_x = target_track_x - self.src_width / 2
                    offset_x = -offset_x
                    offset_y = target_track_y - self.src_height / 2
                    if tw < 100:
                        print("move_forward")
                        self.airplanceApi.move_forward(200)
                    elif tw > 120:
                        print("move_backward")
                        self.airplanceApi.move_backward(200)
                    else:
                        if offset_x < 0:
                            self.airplanceApi.move_right(200)
                            print("move right")
                        else:
                            self.airplanceApi.move_left(200)
                            print("move left")
                else:
                    self.hover()
        except:
            pass
        return src

    def track(self, frame):
        status, coord = self.kcf_tracker.update(frame)
        center = np.array([[np.float32(coord[0] + coord[2] / 2)], [np.float32(coord[1] + coord[3] / 2)]])
        cv2.circle(frame, (center[0], center[1]), 4, (255, 60, 100), 2)
        round_coord = (int(coord[0]), int(coord[1]), int(coord[2]), int(coord[3]))
        return round_coord


if __name__ == '__main__':
    kcf_tracker = KCFTracker()








