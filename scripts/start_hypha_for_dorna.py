from dorna2 import Dorna

import os 
import logging
import squid_control.control.utils_.image_processing as im_processing


import pyqtgraph.dockarea as dock
import time

import argparse
import asyncio
import fractions

import numpy as np
#from av import VideoFrame
from imjoy_rpc.hypha import login, connect_to_server, register_rtc_service

import fractions
import json




dorna_robot = Dorna()
#robot.connect("localhost", "443")
#msg='{"cmd": "jmove", "rel": 1, "j0":50, "vel":10, "accel": 300, "jerk": 1000}'
async def robot_play(msg,context=None):
    #dorna_robot.play(msg=msg)
    print("robot_play")
    print(msg)
    #robot.play(msg=msg)
    return "done"


async def start_service(service_id, workspace=None, token=None):
    client_id = service_id + "-client"
    token = await login({"server_url": "https://ai.imjoy.io",})

    print(f"Starting service...")
    server = await connect_to_server(
        {
            "client_id": client_id,
            "server_url": "https://ai.imjoy.io",
            "workspace": workspace,
            "token": token,
        }
    )
    

    await server.register_service(
        {
            "id": "Dorna2S-control",
            "config":{
                "visibility": "public",
                "run_in_executor": True,
                "require_context": True,   
            },
            "type": "echo",
            "robot_play": robot_play,
        }
    )
    

    

    print(
        f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
    )
    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC demo for video streaming"
    )
    parser.add_argument("--service-id", type=str, default="Dorna2S-control", help="The service id")
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.create_task(start_service(
        args.service_id,
        workspace=None,
        token=None,
    ))
    #loop.create_task(chatbot.connect_server("https://ai.imjoy.io"))
    loop.run_forever()
