import json
from dorna2 import dorna
"""
Use play method to send command to the robot.
There are many ways to call this method
"""
def main(robot):
	# initialize the robot, extend the arm.
    robot.play(msg='{"cmd": "jmove", "rel": 1, "j0":50, "vel":10}')

	# # send a command in text format
	# robot.play(msg='{"cmd": "jmove", "rel": 1, "j0":50, "vel":10}') 	
	# print("Motion is completed")

if __name__ == '__main__':

    robot = dorna.Dorna()
    print("connecting")
    if not robot.connect("localhost", "443"):
        print("not connected")
    else:
        print("connected")
        main(robot)
    robot.close()