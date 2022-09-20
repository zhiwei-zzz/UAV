import cv2
import time
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera

class VideoCapture(object):
    def __init__(self):
        self.camera = PiCamera()
        self.camera.resolution = (320, 240)
        self.camera.framerate = 32
        
        self.src = None
        self.result = None
        self.marker_image = None
        self.display_image = None
        self.src_width = None
        self.src_height = None
        self.track_box = None
        self.detect_box = None
        self.drag_start = None
        self.selection = None        
        
        self.src_window_name = 'Image'
        self.result_window_name = 'Result'
        
        self.cps = 0
        self.cps_values = list()
        self.cps_n_values = 20
        
        self.rawCapture = PiRGBArray(self.camera, size=(320, 240))
        time.sleep(0.2)
        for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
            
            image = frame.array
            start =time.time()
            
            if self.src is None:
                self.src = image.copy()
                self.marker_image = np.zeros_like(image)
                self.src_width = image.shape[1]
                self.src_height = image.shape[0]
                cv2.imshow(self.src_window_name, self.src)
                cv2.setMouseCallback(self.src_window_name, self.onMouse)
            else:
                self.src = image.copy()
                self.marker_image = np.zeros_like(image)
                self.result = self.process_image(self.src)
                self.display_selection()
                self.display_image = cv2.bitwise_or(self.result, self.marker_image)
                if self.track_box is not None and self.is_rect_nonzero(self.track_box):
                    tx, ty, tw, th = self.track_box
                    cv2.rectangle(self.display_image, (tx, ty), (tx+tw, ty+th), (0, 0, 0), 2)
                ###show detect-box###
                elif self.detect_box is not None and self.is_rect_nonzero(self.detect_box):
                    dx, dy, dw, dh = self.detect_box
                    cv2.rectangle(self.display_image, (dx, dy), (dx+dw, dy+dh), (255, 50, 50), 2)
                
                end = time.time()
                self.display_cps(start, end)
                cv2.imshow(self.src_window_name, self.src)
                cv2.imshow(self.result_window_name, self.display_image)
                        
            key = cv2.waitKey(1) & 0xFF
            self.rawCapture.truncate(0)
            if key == ord("q"):
                #self.land()
                break
    
    def process_image(self, image):
        return image
    
    def onMouse(self, event, x, y, flags, params):
        if self.src is None:
            return
        if event == cv2.EVENT_LBUTTONDOWN and not self.drag_start:
            self.track_box = None
            self.detect_box = None
            self.drag_start = (x, y)
        if event == cv2.EVENT_LBUTTONUP:
            self.drag_start = None
            self.detect_box = self.selection
        if self.drag_start:
            xmin = max(0, min(x, self.drag_start[0]))
            ymin = max(0, min(x, self.drag_start[1]))
            xmax = min(self.src_width, max(x, self.drag_start[0]))
            ymax = min(self.src_height, max(y, self.drag_start[1]))
            self.selection = (xmin, ymin, xmax-xmin, ymax-ymin)
    
    def display_selection(self):
        if self.drag_start and self.is_rect_nonzero(self.selection):
            x, y, w, h = self.selection
            cv2.rectangle(self.marker_image, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.rectangle(self.src, (x, y), (x + w, y + h), (0, 255, 255), 2)
    
    def display_cps(self, start, end):
        duration = end - start
        fps = int(1.0/duration)
        self.cps_values.append(fps)
        if len(self.cps_values)>self.cps_n_values:
            self.cps_values.pop(0)
        self.cps = int(sum(self.cps_values)/len(self.cps_values))
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        if self.src_width >= 640:
            vstart = 25
            voffset = int(50+self.src_height/120.)
        elif self.src_width == 320:
            vstart = 15
            voffset = int(35+self.src_height/120.)
        else:
            vstart = 10
            voffset = int(20 + self.src_height / 120.)
        cv2.putText(self.display_image, "CPS: " + str(self.cps), (10, vstart), font_face, font_scale,(255, 255, 0))
        cv2.putText(self.display_image, "RES: " + str(self.src_width) + "X" + str(self.src_height), (10, voffset), font_face, font_scale, (255, 255, 0))       
                    
    def is_rect_nonzero(self, rect):
        try:
            (_,_,w,h) = rect
            return ((w>0)and(h>0))
        except:
            try:
                ((_,_),(w,h),a) = rect
                return (w > 0) and (h > 0)
            except:
                return False    

if __name__ == '__main__':
    video_capture = VideoCapture()