# -*- coding: utf-8 -*-

import cv2

cap = cv2.VideoCapture(0)
ret = cap.set(3, 640)  # 设置帧宽
ret = cap.set(4, 480)  # 设置帧高


class CameraOp():
    def __init__(self):
        self.start_video()


    def start_video(self):
        while cap.isOpened():
            ret, frame = cap.read()
            src = frame.copy()
            result = frame.copy()
            result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            cv2.imshow("result",result)
            cv2.imshow("src",src)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    camreaop = CameraOp()
