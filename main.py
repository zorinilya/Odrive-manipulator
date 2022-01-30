# from __future__ import print_function

import sys
import time
import odrive
from odrive.enums import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import panel


# Current Values Thread
class CurrentValueThread(QtCore.QThread):
    my_signal = QtCore.pyqtSignal()  # QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.flag_stop = False

    def run(self):
        self.flag_stop = True
        while self.flag_stop:
            self.msleep(100)
            self.my_signal.emit()


class ODriveApp(QtWidgets.QMainWindow, panel.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Odrive device search and connection
        self.my_drive = odrive.find_any()
        self.display.append("Bus is " + str(self.my_drive.vbus_voltage) + "V")

        # current values thread start
        self.my_thread = CurrentValueThread()
        self.my_thread.my_signal.connect(self.current_value, QtCore.Qt.QueuedConnection)
        if not self.my_thread.isRunning():
            self.my_thread.start()

        # default modes and parameters
        self.cmbbx_input.addItem("INPUT_MODE_PASSTHROUGH")
        self.cmbbx_input.addItem("INPUT_MODE_POS_FILTER")
        self.cmbbx_input.addItem("INPUT_MODE_TRAP_TRAJ")

        # device calibration
        self.btnCalibration.clicked.connect(self.calibration)

        # position control
        self.buttonGoTo.clicked.connect(self.go_to_position)

        # velocity control
        self.direction = 1
        self.buttonLeft.pressed.connect(lambda: self.run_vel_ctrl(direction=self.direction))
        self.buttonLeft.released.connect(self.stop_vel_ctrl)
        self.buttonRight.pressed.connect(lambda: self.run_vel_ctrl(direction=(-1) * self.direction))
        self.buttonRight.released.connect(self.stop_vel_ctrl)

        # autotuning mode
        self.buttonAutotunStart.clicked.connect(self.autotuning_start)
        self.buttonAutotunStop.clicked.connect(self.autotuning_stop)
        self.buttonReset.clicked.connect(self.autotuning_reset)

    # data update
    def current_value(self):
        t = time.localtime()
        self.display.append("%02d:%02d:%02d " % (t[3], t[4], t[5])
                            + str(format(self.my_drive.axis1.encoder.pos_estimate, '.5f')))
        self.txtCurrentPos.setText(str(format(self.my_drive.axis1.encoder.pos_estimate, '.2f')))
        self.txtCurrentVel.setText(str(format(self.my_drive.axis1.encoder.vel_estimate, '.2f')))
        self.txtCurrentTor.setText(str(format(self.my_drive.axis1.motor.current_control.Iq_measured
                                              * self.my_drive.axis1.motor.config.torque_constant, '.2f')))
        self.txtPhase.setText(str(format(self.my_drive.axis1.controller.autotuning_phase, '.3f')))

    # simultaneous motor and encoder calibration
    def calibration(self):
        self.display.append("Finding odrive...\nStarting calibration...")
        self.my_drive.axis1.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        time.sleep(15)

        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL

        self.display.append("Bus is " + str(self.my_drive.vbus_voltage) + "V")
        self.display.append("Autotuning phase = " + str(self.my_drive.axis1.controller.autotuning_phase))
        self.my_drive.axis1.controller.input_pos = 0
        self.txtCurrentPos.setText(str(self.my_drive.axis1.controller.pos_setpoint))

    def go_to_position(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
        if str(self.cmbbx_input.currentText()) == "INPUT_MODE_POS_FILTER":
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
        elif str(self.cmbbx_input.currentText()) == "INPUT_MODE_TRAP_TRAJ":
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
        else:
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.input_pos = float(self.dblSpnBoxPos.value())

    def run_vel_ctrl(self, direction):
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL

        self.my_drive.axis1.controller.input_vel = direction * self.velocity.value()

    def stop_vel_ctrl(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_IDLE
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_INACTIVE
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_VOLTAGE_CONTROL

    def autotuning_start(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_TUNING

        # self.my_drive.axis1.controller.autotuning_phase = 0
        self.my_drive.axis1.controller.autotuning.frequency = float(self.frequency.value())
        self.my_drive.axis1.controller.autotuning.pos_amplitude = float(self.amplitude.value())

    def autotuning_stop(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_IDLE
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL

    def autotuning_reset(self):
        self.my_drive.axis1.controller.autotuning_phase = 0.000

    def close_event(self, event):
        self.hide()
        self.my_thread.flag_stop = False
        self.my_thread.wait(5000)
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ODriveApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
