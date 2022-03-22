import sys
import time
import odrive
import math
from odrive.enums import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import panel


# This thread runs a function "data_monitoring" that reads data and updates it in GUI
class CurrentValueThread(QtCore.QThread):
    my_signal = QtCore.pyqtSignal()  # QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.flag_stop = False

    def run(self):
        self.flag_stop = True
        while self.flag_stop:
            self.msleep(100)
            self.my_signal.emit()  # The signal runs a function "data_monitoring"


# The main application window class
class ODriveApp(QtWidgets.QMainWindow, panel.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Odrive device search and connection
        self.my_drive = odrive.find_any()  # Run search connected device
        self.display.append("Bus is " + str(self.my_drive.vbus_voltage) + "V")

        # current values thread start
        self.my_thread = CurrentValueThread()
        self.my_thread.my_signal.connect(self.data_monitoring, QtCore.Qt.QueuedConnection)
        if not self.my_thread.isRunning():
            self.my_thread.start()

        # default modes and parameters
        self.cmbbx_input.addItem("INPUT_MODE_PASSTHROUGH")
        self.cmbbx_input.addItem("INPUT_MODE_POS_FILTER")
        self.cmbbx_input.addItem("INPUT_MODE_TRAP_TRAJ")
        self.dblSpnBoxPos.setRange(-999, 1000)

        # device calibration button
        self.btnCalibration.clicked.connect(self.calibration)

        self.buttonGoTo.clicked.connect(lambda: self.requested_position(type_button="GOTO"))
        self.buttonStop_Pos.clicked.connect(lambda: self.requested_position(type_button="STOP"))
        self.buttonHome.clicked.connect(lambda: self.requested_position(type_button="HOME"))

        # velocity control buttons
        self.buttonLeft.pressed.connect(lambda: self.run_vel_control(
            direction=-self.my_drive.axis1.encoder.config.direction
        ))
        self.buttonRight.pressed.connect(lambda: self.run_vel_control(
            direction=self.my_drive.axis1.encoder.config.direction
        ))
        self.buttonLeft.released.connect(self.stop_vel_control)
        self.buttonRight.released.connect(self.stop_vel_control)

        # autotuning mode buttons
        self.buttonAutotunStart.clicked.connect(self.autotuning_start)
        self.buttonAutotunStop.clicked.connect(self.autotuning_stop)
        self.buttonReset.clicked.connect(self.autotuning_reset)

    def set_input_mode(self):
        if str(self.cmbbx_input.currentText()) == "INPUT_MODE_POS_FILTER":
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
        elif str(self.cmbbx_input.currentText()) == "INPUT_MODE_TRAP_TRAJ":
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
        else:
            self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH

    # this function displays reads and updates data in the GUI
    def data_monitoring(self):
        t = time.localtime()
        self.display.append("Time: %02d:%02d:%02d " % (t[3], t[4], t[5])
                            + "    encoder_pos: " + str(format(self.my_drive.axis1.encoder.pos_estimate, '.4f'))
                            + "    pos_setpoint: " + str(format(self.my_drive.axis1.controller.pos_setpoint, '.4f'))
                            )
        self.txtCurrentPos.setText(str(format(self.my_drive.axis1.encoder.pos_estimate, '.4f')))
        self.txtCurrentVel.setText(str(format(self.my_drive.axis1.encoder.vel_estimate, '.4f')))
        self.txtCurrentTor.setText(str(format(self.my_drive.axis1.motor.current_control.Iq_measured
                                              * self.my_drive.axis1.motor.config.torque_constant, '.4f'))
                                   )
        self.txtPhase.setText(str(format(self.my_drive.axis1.controller.autotuning_phase, '.3f')))

    # run of the device calibration
    def calibration(self):
        self.display.append("Finding odrive...\nStarting calibration...")

        # run simultaneous the motor and the encoder calibration
        self.my_drive.axis1.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        time.sleep(15)
        # end of calibration

        # setting operating modes
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
        self.set_input_mode()
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

        # display of calibration results
        self.display.append("Bus is " + str(self.my_drive.vbus_voltage) + "V")
        self.display.append("Autotuning phase = " + str(self.my_drive.axis1.controller.autotuning_phase))

        self.my_drive.axis1.controller.input_pos = 0.0

    def check_for_rotation(self):
        if abs(self.my_drive.axis1.encoder.vel_estimate) > 0.000:
            return True
        else:
            return False

    def requested_position(self, type_button):
        if type_button == "STOP":
            self.my_drive.axis1.requested_state = AXIS_STATE_IDLE
            self.my_drive.axis1.controller.input_pos = self.my_drive.axis1.encoder.pos_estimate
            time.sleep(0.25)
        if not self.check_for_rotation():
            self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
            self.set_input_mode()
            self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
            if type_button == "HOME":
                self.my_drive.axis1.controller.input_pos = 0.0
            elif type_button == "GOTO":
                self.my_drive.axis1.controller.input_pos = self.dblSpnBoxPos.value()

    def run_vel_control(self, direction):
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL

        self.my_drive.axis1.controller.input_vel = direction * self.velocity.value()

    def stop_vel_control(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_IDLE
        self.my_drive.axis1.controller.input_vel = 0.0
        self.my_drive.axis1.controller.input_pos = self.my_drive.axis1.encoder.pos_estimate

        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL

    def autotuning_start(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_TUNING

        self.my_drive.axis1.controller.autotuning.frequency = float(self.frequency.value())
        self.my_drive.axis1.controller.autotuning.pos_amplitude = float(self.amplitude.value())

    def autotuning_stop(self):
        self.my_drive.axis1.requested_state = AXIS_STATE_IDLE
        self.my_drive.axis1.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
        self.my_drive.axis1.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL

    def autotuning_reset(self):
        self.my_drive.axis1.controller.autotuning_phase = 0.0

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
