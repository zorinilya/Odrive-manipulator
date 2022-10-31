# Odrive-manipulator

This project is a 3D printed robotic arm based on brushless motors, 3D printed сycloidal reducer and used control board [ODrive](https://github.com/odriverobotics/ODrive).

To date, one joint of the manipulator has been manufactured and an application has been created with a GUI for setting up the control board and controlling joint in various modes.

## Requirements

- Python 3
- Matplotlib
```
pip install matplotlib
```
- Odrive lib 
``` 
pip install --upgrade odrive
```
- A 12V-58V power supply or battery

## Appearance

![Assembly_1](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/Assembly_1.jpg)

![Assembly_2](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/Assembly_2.jpg)

![test_sample_1](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/test_sample_1.jpg)

![test_sample_2](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/test_sample_2.jpg)

![test_sample_3](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/test_sample_3.jpg)

![test_sample_4](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/test_sample_4.jpg)

## Control board
The control board [ODrive](https://odriverobotics.com/) is used for direct control of brushless motors, setting the modes and operation parameters of brushless motors. The motor controller is a cascaded style position, velocity and current control loop, as per the diagram below. When the control mode is set to position control, the whole loop runs. When running in velocity control mode, the position control part is removed and the velocity command is fed directly in to the second stage input. In torque control mode, only the current controller is used.

![cascaded_control_loop](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/cascaded_control_loop.jpg)

## Drive
Torque is transmitted to the arm joint from a [BLDC](https://www.mad-motor.com/products/mad-components-m6c10-eee.html) through a 3D printed cycloidal gearbox. A magnetic encoder [AS5048A](https://ams.com/as5048a) is used as a position sensor for the motor shaft.

## GUI

![gui](https://github.com/Barsik-Marsik/Odrive-manipulator/blob/master/pics/gui.jpg)

## Tests

[FIrst_test][def]

[def]: https://www.youtube.com/shorts/JeFkW_yjQ3k