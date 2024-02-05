from dorna2 import dorna
import json


def load_sequences(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['sequences']

def execute_action(robot,action):
    # Placeholder for executing an action. Replace with your actual implementation.
    print(f"Executing command: {action['cmd']} with parameters {action}")
    robot.play(action)

def execute_sequence(robot, sequence):
    print(f"Starting sequence: {sequence['description']}")
    for action in sequence['actions']:
        execute_action(robot, action)
    print("Sequence completed.")

def main(robot,file_path):
    sequences = load_sequences(file_path)
    execute_sequence(robot,sequences[0])
    print("All sequences executed.")

if __name__ == '__main__':

    robot = dorna.Dorna()
    
    print("connecting")
    if not robot.connect("192.168.137.155", "443"):
        print("not connected")
    else:
        print("connected")
        robot.set_motor(1)
        file_path = 'dorna2/path/test_path.json'
        main(robot,file_path)
    robot.close()