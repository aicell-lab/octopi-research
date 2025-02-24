from dorna2 import Dorna
import time

def move_sample_from_microscope_to_incubator(timeout=60):
    robot = Dorna()
    
    robot.connect("192.168.2.20")
    print("Connected to robot")
    robot.set_motor(1)
    # Add your robotic arm movement script here
    print("Playing script")
    robot.play_script("microscope_to_incubator.txt", timeout=timeout)
        

def move_sample_from_incubator_to_microscope(timeout=60):
    robot = Dorna()
    robot.connect("192.168.2.20")
    print("Connected to robot")
    robot.set_motor(1)
    # Add your robotic arm movement script here
    print("Playing script")
    robot.play_script("incubator_to_microscope.txt",timeout=timeout)
