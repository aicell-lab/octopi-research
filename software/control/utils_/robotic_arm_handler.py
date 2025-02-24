from dorna2 import Dorna
import time

def move_sample_from_microscope_to_incubator(timeout=60):
    robot = Dorna()
    try:
        robot.connect("192.168.2.20")
        # Add your robotic arm movement script here
        robot.play_script("microscope_to_incubator.txt")
        time.sleep(timeout)
    finally:
        robot.close()

def move_sample_from_incubator_to_microscope(timeout=60):
    robot = Dorna()
    try:
        robot.connect("192.168.2.20")
        # Add your robotic arm movement script here
        robot.play_script("incubator_to_microscope.txt")
        time.sleep(timeout)
    finally:
        robot.close()