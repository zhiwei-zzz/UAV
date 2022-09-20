# -*- coding: utf-8 -*-

from tkinter import *
import time
from connect_uav import UPUavControl
import threading

class MY_GUI():
    def __init__(self,init_window_name):
        self.init_window_name = init_window_name
        self.airplanceApi = UPUavControl()
        self.current_height = 0
        self.set_init_window()
        time.sleep(1)
        self.airplanceApi.get_air_height()
        getDataThread = threading.Thread(name="send_thread", target=self.get_data)
        getDataThread.setDaemon(True)
        getDataThread.start()

    # 获取当前高度
    def get_data(self):
        while True:
            self.current_height = self.airplanceApi.get_current_height()
            self.current_height_text.config(text=self.current_height)

    #设置窗口
    def set_init_window(self):
        self.init_window_name.title("onekey_takeoff")           #窗口名
        self.init_window_name.geometry('480x180+10+10')

        self.init_data_label = Label(self.init_window_name, text="当前高度:",font=("Arial",16))
        self.init_data_label.grid(row=0, column=8)
        self.current_height_text = Label(self.init_window_name, text="0cm",font=("Arial",16))
        self.current_height_text.grid(row=0, column=9)
        self.result_data_label = Label(self.init_window_name, text="目标高度:",font=("Arial",16))
        self.result_data_label.grid(row=2, column=8)
        #文本框
        self.init_data_Text = Text(self.init_window_name, width=16, height=1,font=("Arial",16))  #原始数据录入框
        self.init_data_Text.grid(row=2, column=9, rowspan=1, columnspan=1)
        #按钮
        self.btn_onekey_takeoff = Button(self.init_window_name, font=("Arial",16),text="一键起飞", bg="lightblue", width=10,command=self.onekey_takeoff)  # 调用内部方法  加()为直接调用
        self.btn_onekey_takeoff.grid(row=4, column=9)
        # 按钮
        self.btn_onekey_landed = Button(self.init_window_name, font=("Arial",16),text="一键降落", bg="lightblue", width=10,
                                              command=self.onekey_landed)  # 调用内部方法  加()为直接调用
        self.btn_onekey_landed.grid(row=8, column=9)


    #功能函数
    def onekey_takeoff(self):
        height = int(self.init_data_Text.get(1.0,END).strip().replace("\n","").encode())
        self.airplanceApi.stop()
        time.sleep(1)
        self.airplanceApi.unclock()
        time.sleep(2)
        self.airplanceApi.set_height(height)


    # 功能函数
    def onekey_landed(self):
        self.airplanceApi.land()
        self.airplanceApi.set_height(0)



def gui_start():
    init_window = Tk()
    ZMJ_PORTAL = MY_GUI(init_window)

    init_window.mainloop()
gui_start()