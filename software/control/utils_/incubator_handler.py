import time
import asyncio
from hypha_rpc.sync import connect_to_server

server_url = "http://192.168.2.1:9527"
service_id = "ws-user-pine-bumper-79360175/izm2rHYVhXeUqPDcateLHt:incubator-control"
def wait_until_not_busy(timeout=50):
    server = connect_to_server({"server_url": server_url})
    svc = server.get_service(service_id)
    
    while svc.is_busy():
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            raise TimeoutError("Timeout reached")

def send_initialize_command_incubator():
    server = connect_to_server({"server_url": server_url})
    svc = server.get_service(service_id)
    wait_until_not_busy(timeout=50)
    svc.initialize()

def put_sample_from_transfer_station_to_slot(slot=5):
    server = connect_to_server({"server_url": server_url})
    svc = server.get_service(service_id)
    wait_until_not_busy(timeout=50)
    svc.put_sample_from_transfer_station_to_slot(slot)
    wait_until_not_busy(timeout=50)

def get_sample_from_slot_to_transfer_station(slot=5):
    server = connect_to_server({"server_url": server_url})
    svc = server.get_service(service_id)
    wait_until_not_busy(timeout=50)
    svc.get_sample_from_slot_to_transfer_station(slot)
    wait_until_not_busy(timeout=50)

if __name__ == "__main__":
    put_sample_from_transfer_station_to_slot(5)
    get_sample_from_slot_to_transfer_station(5)