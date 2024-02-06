from dorna2 import dorna
import json
from squid_control.squid_controller import SquidController

def load_sequences(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['sequences']

def execute_action(robot,action):
    # Placeholder for executing an action. Replace with your actual implementation.
    print(f"Executing command: {action['cmd']} with parameters {action}")
    #robot.play(action)

def execute_sequence(robot, sequence):
    print(f"Starting sequence: {sequence['description']}")
    for action in sequence['actions']:
        execute_action(robot, action)
    print("Sequence completed.")

def main(squid,robot,file_path):
    sequences = load_sequences(file_path)

    squid.init_stage()
    print("Stage is at the zero position.")

    #intialize the robot
    execute_sequence(robot,sequences[0])
    # Then the robot grab the sample
    execute_sequence(robot,sequences[1])
    # Then the robot place the sample on the microscope stage
    execute_sequence(robot,sequences[2])
    # Then the microscope scan the sample
    squid.move_to_scaning_position()
    #squid.plate_scan()
    squid.init_stage()
    #After the sample scanned, the robot pick the sample
    execute_sequence(robot,sequences[3])
    print("All sequences executed.")

if __name__ == '__main__':

    robot = dorna.Dorna()
    squid = SquidController(is_simulation=True)
    
    print("connecting")
    if not robot.connect("192.168.137.155", "443"):
        print("not connected")
    else:
        print("connected")
        robot.set_motor(1)
    file_path = 'dorna2/path/test_path.json'
    main(squid,robot,file_path)
    robot.close()