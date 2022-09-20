# -*- coding: utf-8 -*-
class PID_t:

    def __init__(self):
        self.d_limit = 100.0
        self.limit = 10.0

        #pid数据值
        self.err = 0.0
        self.exp_old = 0.0
        self.feedback_old = 0.0
        self.fb_d = 0.0
        self.fb_d_ex = 0.0
        self.exp_d = 0.0
        self.err_i = 0.0
        self.ff = 0.0
        self.pre_d = 0.0
        self.out = 0.0

        #pid参数值
        self.fb_d_mode = 0
        self.kp = 1.3
        self.ki = 0.01
        self.kd_ex = 0.0
        self.kd_fb = 0.0
        self.k_ff = 0.0
        self.inc_hz = 0.0



    def pid_calculate(self,dts,in_ff,expect,feedback):

        if dts != 0:
            dts = 1 / dts
        self.exp_d = (expect - self.exp_old) * dts
        if self.fb_d_mode == 0:
            self.fb_d = (feedback - self.feedback_old) * dts
        else:
            self.fb_d = self.fb_d

        differential = (self.kd_ex * self.exp_d - self.kd_fb * self.fb_d)
        self.err = (expect - feedback)

        if self.err > self.d_limit:
            self.err = self.d_limit
        elif self.err < -self.d_limit:
            self.err = -self.d_limit

        self.err_i += self.ki * self.err

        if self.err_i > self.limit:
            self.err_i = self.limit
        elif self.err_i < -self.limit:
            self.err_i = -self.limit
        self.out = self.k_ff * in_ff + self.kp * self.err + differential + self.err_i
        self.feedback_old = feedback
        self.exp_old = expect
        return self.out

if __name__ == '__main__':
    pid = PID_t()
    speed = round(pid.pid_calculate(0.001,0,70,22))
    print(speed)
    
