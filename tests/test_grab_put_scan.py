import logging
from dorna2 import dorna
from squid_control.squid_controller import SquidController

robot = dorna.Dorna()
squid = SquidController(is_simulation=True)

def zero_stage():
    #move the stage to the zero position for loading or unloading samples
    logging.info("Moving the stage to the zero position.")
    squid.init_stage()
    logging.info("Stage is at the zero position.")

def init_robot():
    # Code to initialize the robotic arm
    logging.info("Connecting to the robot.")
    if not robot.connect("localhost", "443"):
        logging.error("Failed to connect to the robot.")
        raise Exception("Failed to connect to the robot.")
    else:
        robot.set_motor(1)
        logging.info("Connected to the robot, motor is on.")

def grab_


def main():
    try:


        logging.info("Arm grabbing the sample.")
        grab()

        logging.info("Placing the sample on the microscope stage.")
        put_to_stage()

        logging.info("Arm turning away and waiting.")
        turn_away()

        logging.info("Microscope scanning the sample.")
        scan()

        logging.info("Arm turning back.")
        turn_back()

        logging.info("Picking the sample after scan.")
        pick_after_scan()

        logging.info("Putting back the sample.")
        put_back()

        logging.info("Procedure completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        # Additional error handling or recovery code

if __name__ == "__main__":
    main()
