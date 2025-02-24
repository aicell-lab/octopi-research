from cytomat import Cytomat
import time

def put_sample_from_transfer_station_to_slot(slot=5):
    c = Cytomat("ttyACM0")
    c.wait_until_not_busy(timeout=50)
    c.plate_handler.move_plate_from_transfer_station_to_slot(slot)
    c.wait_until_not_busy(timeout=50)

def get_sample_from_slot_to_transfer_station(slot=5):
    c = Cytomat("ttyACM0")
    c.wait_until_not_busy(timeout=50)
    c.plate_handler.move_plate_from_slot_to_transfer_station(slot)
    c.wait_until_not_busy(timeout=50)