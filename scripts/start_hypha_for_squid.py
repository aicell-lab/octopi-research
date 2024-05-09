import os 
import logging
import squid_control.control.utils_.image_processing as im_processing


import pyqtgraph.dockarea as dock
import time
from hypha_storage import HyphaDataStore
import argparse
import asyncio
import fractions

import numpy as np
#from av import VideoFrame
from imjoy_rpc.hypha import login, connect_to_server, register_rtc_service
#from imjoy_rpc.hypha.sync import register_rtc_service
#import aiortc
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration

from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions
import json
import webbrowser
from squid_control.squid_controller import SquidController
#import squid_control.squid_chatbot as chatbot
import cv2

current_x, current_y = 0,0

squidController= SquidController(is_simulation=True)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from another track.
    """

    kind = "video"

    def __init__(self):
        super().__init__()  # don't forget this!
        self.count = 0

    async def recv(self):
        # Read frame from squid controller, now correctly formatted as BGR
        bgr_img = one_new_frame()
        # Create the video frame
        new_frame = VideoFrame.from_ndarray(bgr_img, format="bgr24")
        new_frame.pts = self.count
        new_frame.time_base = fractions.Fraction(1, 1000)
        self.count += 1
        await asyncio.sleep(1)  # Simulating frame rate delay
        return new_frame



async def send_status(data_channel, workspace=None, token=None):
    """
    Send the current status of the microscope to the client. User can dump information of the microscope to a json data.
    ----------------------------------------------------------------
    Parameters
    ----------
    data_channel : aiortc.DataChannel
        The data channel to send the status to.
    workspace : str, optional
        The workspace to use. The default is None.
    token : str, optional
        The token to use. The default is None.

    Returns
    -------
    None.
    """
    while True:
        if data_channel and data_channel.readyState == "open":
            global current_x, current_y
            current_x, current_y, current_z, current_theta, is_illumination, _ = get_status()
            squid_status = {"x": current_x, "y": current_y, "z": current_z, "theta": current_theta, "illumination": is_illumination}
            data_channel.send(json.dumps(squid_status))
        await asyncio.sleep(1)  # Wait for 1 second before sending the next update


def move_by_distance(x,y,z, context=None):
    """
    Move the stage by a distance in x,y,z axis.
    ----------------------------------------------------------------
    Parameters
    ----------
    x : float
        The distance to move in x axis.
    y : float
        The distance to move in y axis.
    z : float
        The distance to move in z axis.
    context : dict, optional
            The context is a dictionary contains the following keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
    """
    squidController.navigationController.move_x(x)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    squidController.navigationController.move_y(y)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    squidController.navigationController.move_z(z)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print(f'The stage moved ({x},{y},{z})mm through x,y,z axis')


        
def move_to_position(x,y,z, context=None):
    """
    Move the stage to a position in x,y,z axis.
    ----------------------------------------------------------------
    Parameters
    ----------
    x : float
        The distance to move in x axis.
    y : float
        The distance to move in y axis.
    z : float
        The distance to move in z axis.
    context : dict, optional
            The context is a dictionary contains keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
            For detailes, see: https://ha.amun.ai/#/

    """
    if x != 0:
        squidController.navigationController.move_x_to(x)
        while squidController.microcontroller.is_busy():
            time.sleep(0.005)
    if y != 0:        
        squidController.navigationController.move_y_to(y)
        while squidController.microcontroller.is_busy():
            time.sleep(0.005)
    if z != 0:    
        squidController.navigationController.move_z_to(z)
        while squidController.microcontroller.is_busy():
            time.sleep(0.005)
    print(f'The stage moved to position ({x},{y},{z})mm')


def get_status(context=None):
    """
    Get the current status of the microscope.
    ----------------------------------------------------------------
    Parameters
    ----------
        context : dict, optional
            The context is a dictionary contains keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
            For detailes, see: https://ha.amun.ai/#/

    Returns
    -------
    current_x : float
        The current position of the stage in x axis.
    current_y : float
        The current position of the stage in y axis.
    current_z : float
        The current position of the stage in z axis.
    current_theta : float
        The current position of the stage in theta axis.
    is_illumination_on : bool
        The status of the bright field illumination.

    """
    current_x, current_y, current_z, current_theta = squidController.navigationController.update_pos(microcontroller=squidController.microcontroller)
    is_illumination_on = squidController.liveController.illumination_on
    scan_channel = squidController.multipointController.selected_configurations
    return current_x, current_y, current_z, current_theta, is_illumination_on,scan_channel


def one_new_frame(context=None):
    gray_img = squidController.camera.read_frame()
    bgr_img = np.stack((gray_img,)*3, axis=-1)  # Duplicate grayscale data across 3 channels to simulate BGR format.
    return bgr_img


def snap(context=None):
    """
    Get the current frame from the camera, converted to a 3-channel BGR image.
    """
    squidController.camera.send_trigger()
    squidController.liveController.turn_on_illumination()
    squidController.liveController.set_illumination(0,44)
    if squidController.microcontroller.is_busy():
        time.sleep(0.05)
    gray_img = squidController.camera.read_frame()
    time.sleep(0.05)
    #squidController.liveController.set_illumination(0,0)
    if squidController.microcontroller.is_busy():
        time.sleep(0.005)
    squidController.liveController.turn_off_illumination()
    #gray_img=np.resize(gray_img,(512,512))
    # Rescale the image to span the full 0-255 range
    min_val = np.min(gray_img)
    max_val = np.max(gray_img)
    if max_val > min_val:  # Avoid division by zero if the image is completely uniform
        gray_img = (gray_img - min_val) * (255 / (max_val - min_val))
        gray_img = gray_img.astype(np.uint8)  # Convert to 8-bit image
    else:
        gray_img = np.zeros((512, 512), dtype=np.uint8)  # If no variation, return a black image

    bgr_img = np.stack((gray_img,)*3, axis=-1)  # Duplicate grayscale data across 3 channels to simulate BGR format.
    _, png_image = cv2.imencode('.png', bgr_img)
    # Store the PNG image
    file_id = datastore.put('file', png_image.tobytes(), 'snapshot.png', "Captured microscope image in PNG format")
    print(f'The image is snapped and saved as {datastore.get_url(file_id)}')
    return datastore.get_url(file_id)


def open_illumination(context=None):
    """
    Turn on the bright field illumination.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    squidController.liveController.turn_on_illumination()

def close_illumination(context=None):
    """
    Turn off the bright field illumination.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    squidController.liveController.turn_off_illumination()

def scan_well_plate(context=None):
    """
    Scan the well plate accroding to pre-defined position list.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    print("Start scanning well plate")
    squidController.scan_well_plate(action_ID='Test')

def set_illumination(illumination_source,intensity, context=None):
    """
    Set the intensity of the bright field illumination.
    illumination_source : int
    intensity : float, 0-100
    If you want to know the illumination source's and intensity's number, you can check the 'channel_configurations.xml' file.
    """
    squidController.liveController.set_illumination(illumination_source,intensity)
    print(f'The intensity of the {illumination_source} illumination is set to {intensity}.')

def set_camera_exposure(exposure_time, context=None):
    """
    Set the exposure time of the camera.
    exposure_time : float, 
    """
    squidController.camera.set_exposure_time(exposure_time)
    print(f'The exposure time of the camera is set to {exposure_time}.')


def stop_scan(context=None):
    """
    Stop the well plate scanning.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    squidController.liveController.stop_live()
    print("Stop scanning well plate")
    pass

def home_x(context=None):
    """
    Move the stage to the home position in x axis.

    """
    squidController.navigationController.home_x(0)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to home position in x axis')

def home_y(context=None):
    """
    Move the stage to the home position in y axis.

    """
    squidController.navigationController.home_y(0)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to home position in y axis')

def home_z(context=None):
    """
    Move the stage to the home position in z axis.

    """
    squidController.navigationController.home_z(0)
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to home position in z axis')

def zero_x(context=None):
    """
    Move the stage to the zero position in x axis.

    """
    squidController.navigationController.zero_x()
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to zero position in x axis')

def zero_y(context=None):
    """
    Move the stage to the zero position in y axis.

    """
    squidController.navigationController.zero_y()
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to zero position in y axis')

def zero_z(context=None):
    """
    Move the stage to the zero position in z axis.

    """
    squidController.navigationController.zero_z()
    while squidController.microcontroller.is_busy():
        time.sleep(0.005)
    print('The stage moved to zero position in z axis')


def move_to_zero_position(context=None):
    """
    Move the stage to the loading position.

    """
    squidController.slidePositionController.move_to_slide_loading_position()
    print('The stage moved to loading position')

def auto_focus(context=None):
    """
    Auto focus the camera.

    """
    squidController.do_autofocus()
    print('The camera is auto focused')

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
    
    # async def on_init(peer_connection):
    #     @peer_connection.on("track")
    #     def on_track(track):
    #         squidController.camera.send_trigger()
    #         squidController.liveController.turn_on_illumination()
    #         squidController.liveController.set_illumination(0,44)
    #         if squidController.microcontroller.is_busy():
    #             time.sleep(0.05)
    #         print(f"Track {track.kind} received")

    #         peer_connection.addTrack(
    #             VideoTransformTrack()
    #         )
         
    #         @track.on("ended")
    #         async def on_ended():
    #             squidController.liveController.turn_off_illumination()
    #             if squidController.microcontroller.is_busy():
    #                 time.sleep(0.05)
    #             print(f"Track {track.kind} ended")
    
    #     data_channel = peer_connection.createDataChannel("microscopeStatus")
    #     # Start the task to send stage position periodically
    #     asyncio.create_task(send_status(data_channel))

    await server.register_service(
        {
            "id": "microscope-control-squid",
            "config":{
                "visibility": "public",
                "run_in_executor": True,
                "require_context": True,   
            },
            "type": "echo",
            "move_by_distance": move_by_distance,
            "snap": snap,
            "off_illumination": close_illumination,
            "on_illumination": open_illumination,
            "scan_well_plate": scan_well_plate,
            "stop_scan": stop_scan,
            "home_x": home_x,
            "home_y": home_y,
            "home_z": home_z,
            "zero_x": zero_x,
            "zero_y": zero_y,
            "zero_z": zero_z,
            "move_to_position": move_to_position,      
            "move_to_zero_position": move_to_zero_position,
            "auto_focus": auto_focus,
        }
    )
    
    await register_rtc_service(
        server,
        service_id=service_id,
        config={
            "visibility": "public",
            #"on_init": on_init,
        },
    )
    global datastore
    datastore = HyphaDataStore()
    await datastore.setup(server, service_id="data-store")

    print(
        f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
    )
    print(f"You can access the webrtc stream at https://aicell-lab.github.io/squid-control/?service_id={service_id}")
    
    #await chatbot.connect_server("https://ai.imjoy.io")



# Now define chatbot services

def get_schema():
    return {
        "move_by_distance": {
            "type": "bioimageio-chatbot-extension",
            "title": "move_by_distance",
            "description": "Move the stage by a specified distance in millimeters, the stage will move along the X, Y, and Z axes. You must retur all three numbers. You also must return 0 if you don't to move the stage along that axis. Notice: for new well plate imaging, move the Z axis to 4.1mm can reach the focus position. And the maximum value of Z axis is 5mm.",
            "properties": {
                "x": {"type": "number", "description": "Move the stage along X axis, default is 0."},
                "y": {"type": "number", "description": "Move the stage along Y axis, default is 0."},
                "z": {"type": "number", "description": "Move the stage along Z axis,default is 0."},
            },
        },
        "move_to_position": {
            "type": "bioimageio-chatbot-extension",
            "title": "move_to_position",
            "description": "Move the stage to a specified position in millimeters, the stage will move to the specified X, Y, and Z coordinates. You must retur all three numbers. You also must return 0 if you don't to move the stage along that axis.",
            "properties": {
                "x": {"type": "number", "description": "Move the stage to the X coordinate, default is 0."},
                "y": {"type": "number", "description": "Move the stage to the Y coordinate, default is 0."},
                "z": {"type": "number", "description": "Move the stage to the Z coordinate, default is 0."},
            },
        },
        "auto_focus": {
            "type": "bioimageio-chatbot-extension",
            "title": "auto_focus",
            "description": "Autofocus the microscope, the value returned is just 1. If this action is required, it will execute before snapping an image.",
            "properties": {
                "N": {"type": "number", "description": "Default value:10. This parameter represents the number of discrete focus positions that the autofocus algorithm evaluates to determine the optimal focus."},
                "delta_Z": {"type": "number", "description": "Default value: 1.524. This parameter defines the step size in the Z-axis between each focus position checked by the autofocus routine, and the unit is in micrometers."},
            },
        },
        "snap_image": {
            "type": "bioimageio-chatbot-extension",
            "title": "snap_image",
            "description": "Snap an image from the microscope with specified exposure time. The value returned is the URL of the image.",
            "properties": {
                "exposure": {"type": "number", "description": "Set the microscope camera's exposure time in milliseconds."},
            },
        },
        "move_to_zero_position": {   
            "type": "bioimageio-chatbot-extension",
            "title": "move_to_zero_position",
            "description": "When sample need to be loaded or unloaded, move the stage to the zero position so that the robotic arm can reach the sample.",
        },
    }


def move_to_position_schema(config):
    print("Moving the stage to position:", config)
    if config["x"] is None:
        config["x"] = 0
    if config["y"] is None:
        config["y"] = 0
    if config["z"] is None:
        config["z"] = 0
    elif config["z"] > 4.7 or config["z"] < 0.0:
        error = "The Z axis is out of range, the maximum value is 5."
        return {"error": error}
    move_to_position(config["x"], config["y"], config["z"])
    return {"result": "Moved the stage!"}

def move_by_distance_schema(config):
    print("Moving the stage by distance:", config)
    if config["x"] is None:
        config["x"] = 0
    if config["y"] is None:
        config["y"] = 0
    if config["z"] is None:
        config["z"] = 0
    move_by_distance(config["x"], config["y"], config["z"])
    return {"result": "Moved the stage!"}

def auto_focus_schema(config):
    auto_focus()
    return {"result": "Auto focused!"}
def snap_image_schema(config):
    squid_image_url = snap()
    resp = f"![Image]({squid_image_url})"
    return resp

async def setup():
    
    chatbot_extension = {
        "_rintf": True,
        "id": "squid-control",
        "type": "bioimageio-chatbot-extension",
        "name": "Squid Microscope Control",
        "description": "You are a chatbot majoring a microscope. Your mission is answering the user's questions, and also controlling the microscope according to the user's commands. Remember, you are controlling a real microscope, distinguish the questions and commands, and execute them correctly.",
        "get_schema": get_schema,
        "tools": {
            "move_by_distance": move_by_distance_schema,
            "move_to_position": move_to_position_schema, 
            "auto_focus": auto_focus_schema, 
            "snap_image": snap_image_schema,
        }
    }


    server_url = "https://chat.bioimage.io"
    token = await login({"server_url": server_url})
    server = await connect_to_server({"server_url": server_url, "token": token})
    svc = await server.register_service(chatbot_extension)
    print(f"Extension service registered with id: {svc.id}, you can visit the service at: https://bioimage.io/chat?server={server_url}&extension={svc.id}")









if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC demo for video streaming"
    )
    parser.add_argument("--simulation", type=bool, default=True, help="The simulation mode")
    parser.add_argument("--service-id", type=str, default="squid-control", help="The service id")
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
    loop.create_task(setup())

    

    loop.run_forever()
