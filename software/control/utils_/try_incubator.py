from cytomat import Cytomat

c = Cytomat("ttyACM0")

print("Plate on transfer station?", c.overview_status.transfer_station_occupied)
# range from 42 to 22, step -1
for i in range(21, 19, -1):

    c.wait_until_not_busy(timeout=50)
    c.plate_handler.move_plate_from_transfer_station_to_slot(i)
    c.wait_until_not_busy(timeout=50)
    c.plate_handler.move_plate_from_slot_to_transfer_station(i)
    c.wait_until_not_busy(timeout=50)
