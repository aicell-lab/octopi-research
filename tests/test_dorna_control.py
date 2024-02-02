from dorna2 import dorna
"""
Use play method to send command to the robot.
There are many ways to call this method
"""

def main(robot):
    # Now ready to pick the well plate on the table
    robot.play(timeout=20, cmd="jmove", rel=0, j0=-5.581055, j1=27.202148, j2=-112.324219, j3=1.889648, j4=-0.395508, j5=0.85, vel=15)
    #{"cmd":"jmove","rel":0,"j0":-8.481445,"j1":27.13623,"j2":-111.51123,"j3":1.120605,"j4":-0.395508}
    # pick and push
    robot.play(timeout=20, cmd="lmove", rel=0, x=293.52175, y=-36, z=71.617313, a=-83.232422, b=-4.526367, c=0.85, vel=30)
    robot.play(timeout=20, cmd="lmove", rel=0, x=304, y=-36, z=72.285919, a=-83.254395, b=-4.526367, c=-50, vel=30)
    
    # Grab
    robot.play(timeout=20, cmd="lmove", rel=0, x=304, y=-36, z=72.285919, a=-83.254395, b=-4.526367, c=-96.31625, vel=30)

    # Lift
    robot.play(timeout=20, cmd="lmove", rel=0, x=160.351271, y=-32.34358, z=409.673431, a=-83.210449, b=-0.395508, c=-96.3175, vel=50)

    # Turn to the microscope
    robot.play(timeout=20, cmd="jmove", rel=0, j0=97.207031, j1=113.334961, j2=-92.922363, j3=-103.64502, j4=-0.395508, j5=-96.3175, vel=15)

    # This is the position over the stage.
    robot.play(timeout=20, cmd="lmove", rel=0, x=-54.53445, y=185.655446, z=411.375911, a=-83.254395, b=22.214355, c=-96.3175, vel=10)

    # Put the well plate
    robot.play(timeout=20, cmd="lmove", rel=0, x=-52.59368, y=182.144001, z=403.170829, a=-83.276367, b=21.577148, c=-96.3175, vel=5)
    robot.play(timeout=20, cmd="lmove", rel=0, x=-52.59368, y=182.144001, z=386, a=-83.276367, b=21.577148, c=-96.3175, vel=5)

    # Lose the grab
    robot.play(timeout=20, cmd="lmove", rel=0, x=-52.853176, y=182.779671, z=386, a=-83.29834, b=21.577148, c=-60, vel=30)

    # lift the empty gripper
    robot.play(timeout=20, cmd="lmove", rel=0, x=-52.853176, y=182.779671, z=403.562931, a=-83.29834, b=21.577148, c=-58.3275, vel=10)

    # Turn away
    robot.play(timeout=20, cmd="jmove", rel=0, j0=-3.625488, vel=15)

    # Go back
    robot.play(timeout=20, cmd="jmove", rel=0, j0=105.622559, vel=15)

    # Over the well plate
    robot.play(timeout=20, cmd="lmove", rel=0, x=-53.295679, y=180, z=406.000237, a=-83.276367, b=22.192383, c=-59.99875, vel=10)

    # Go to for grabbing the well plate
    robot.play(timeout=20, cmd="lmove", rel=0, x=-53.351025, y=181, z=387.502854, a=-83.276367, b=22.214355, c=-59.99875, vel=10)

    # Grab
    robot.play(timeout=20, cmd="lmove", rel=0, x=-53.297361, y=183, z=386.3, a=-83.29834, b=22.214355, c=-98, vel=30)
        # lift, notice, move y 1.5mm when lifting.
    robot.play(timeout=20, cmd="lmove", rel=0, x=-53.328183, y=181, z=397.919173, a=-83.29834, b=22.214355, c=-98, vel=10)
    robot.play(timeout=20, cmd="lmove", rel=0, x=-53.325128, y=181, z=410.485635, a=-83.29834, b=22.214355, c=-98, vel=10)

    # Turn back
    robot.play(timeout=20, cmd="jmove", rel=0, j0=0.769043, j1=105.380859, j2=-88.330078, j3=-100.349121, j4=22.214355, j5=-97, vel=15)

    # Over the storage place
    robot.play(timeout=20, cmd="jmove", rel=0, j0=-5.581055, j1=27.202148, j2=-112.324219, j3=1.889648, j4=-0.395508, j5=-96.6675, vel=30)

    # Put
    robot.play(timeout=20, cmd="lmove", rel=0, x=304, y=-36, z=72.285919, a=-83.254395, b=-4.526367, c=-96.31625, vel=30)
    robot.play(timeout=20, cmd="lmove", rel=0, x=304, y=-36, z=72.285919, a=-83.254395, b=-4.526367, c=-10, vel=30)

if __name__ == '__main__':

    robot = dorna.Dorna()
    print("connecting")
    if not robot.connect("192.168.137.155", "443"):
        print("not connected")
    else:
        print("connected")
        main(robot)
    robot.close()