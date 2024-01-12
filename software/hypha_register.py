import os 
# app specific libraries
import control.camera as camera
import control.core_reef as core
import control.microcontroller as microcontroller
from control._def import *
import logging
import control.serial_peripherals as serial_peripherals

if SUPPORT_LASER_AUTOFOCUS:
    import control.core_displacement_measurement as core_displacement_measurement

import pyqtgraph.dockarea as dock
import time

import cv2
import threading
import argparse
import asyncio
import os
import uuid
import fractions
import tifffile as tif

import numpy as np
#from av import VideoFrame
from imjoy_rpc.hypha import login, connect_to_server, register_rtc_service
#from imjoy_rpc.hypha.sync import register_rtc_service
#import aiortc
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration
from PyQt5.QtCore import QThread, pyqtSignal

from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions

import webbrowser

class SquidController:
    # variables
    fps_software_trigger= 100

    def __init__(self,is_simulation = True, *args, **kwargs):
        super().__init__(*args,**kwargs)

        #load objects
        if is_simulation:
            if ENABLE_SPINNING_DISK_CONFOCAL:
                self.xlight = serial_peripherals.XLight_Simulation()
            if SUPPORT_LASER_AUTOFOCUS:
                self.camera = camera.Camera_Simulation(rotate_image_angle = ROTATE_IMAGE_ANGLE, flip_image=FLIP_IMAGE)
                self.camera_focus = camera.Camera_Simulation()
            else:
                self.camera = camera.Camera_Simulation(rotate_image_angle = ROTATE_IMAGE_ANGLE, flip_image=FLIP_IMAGE)
            self.microcontroller = microcontroller.Microcontroller_Simulation()
        else:
            if ENABLE_SPINNING_DISK_CONFOCAL:
                self.xlight = serial_peripherals.xlight()
            try:
                if SUPPORT_LASER_AUTOFOCUS:
                    sn_camera_main = camera.get_sn_by_model(MAIN_CAMERA_MODEL)
                    sn_camera_focus = camera.get_sn_by_model(FOCUS_CAMERA_MODEL)
                    self.camera = camera.Camera(sn=sn_camera_main,rotate_image_angle=ROTATE_IMAGE_ANGLE,flip_image=FLIP_IMAGE)
                    self.camera.open()
                    self.camera_focus = camera.Camera(sn=sn_camera_focus)
                    self.camera_focus.open()
                else:
                    self.camera = camera.Camera(rotate_image_angle=ROTATE_IMAGE_ANGLE,flip_image=FLIP_IMAGE)
                    self.camera.open()
            except:
                if SUPPORT_LASER_AUTOFOCUS:
                    self.camera = camera.Camera_Simulation(rotate_image_angle=ROTATE_IMAGE_ANGLE,flip_image=FLIP_IMAGE)
                    self.camera.open()
                    self.camera_focus = camera.Camera_Simulation()
                    self.camera_focus.open()
                else:
                    self.camera = camera.Camera_Simulation(rotate_image_angle=ROTATE_IMAGE_ANGLE,flip_image=FLIP_IMAGE)
                    self.camera.open()
                print('! camera not detected, using simulated camera !')
            self.microcontroller = microcontroller.Microcontroller(version=CONTROLLER_VERSION)

        # reset the MCU
        self.microcontroller.reset()

        # reinitialize motor deivers and DAC  (in particular for V2.1 driver board where PG is not functional)
        self.microcontroller.initialize_drivers()
        
        # configure the actuators
        self.microcontroller.configure_actuators()

        self.configurationManager = core.ConfigurationManager(filename='./channel_configurations.xml')

        self.streamHandler = core.StreamHandler(display_resolution_scaling=DEFAULT_DISPLAY_CROP/100)
        self.liveController = core.LiveController(self.camera,self.microcontroller,self.configurationManager)
        self.navigationController = core.NavigationController(self.microcontroller)
        self.slidePositionController = core.SlidePositionController(self.navigationController,self.liveController,is_for_wellplate=True)
        self.autofocusController = core.AutoFocusController(self.camera,self.navigationController,self.liveController)
        self.scanCoordinates = core.ScanCoordinates()
        self.multipointController = core.MultiPointController(self.camera,self.navigationController,self.liveController,self.autofocusController,self.configurationManager,scanCoordinates=self.scanCoordinates,parent=self)
        if ENABLE_TRACKING:
            self.trackingController = core.TrackingController(self.camera,self.microcontroller,self.navigationController,self.configurationManager,self.liveController,self.autofocusController,self.imageDisplayWindow)
        #self.imageSaver = core.ImageSaver()
        #self.imageDisplay = core.ImageDisplay()
        #self.navigationViewer = core.NavigationViewer(sample=str(WELLPLATE_FORMAT)+' well plate')

        #self.multiPointWorker = core.MultiPointWorker(self.multipointController)
        # retract the object
        self.navigationController.home_z()
        # wait for the operation to finish
        t0 = time.time()
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 10:
                print('z homing timeout, the program will exit')
                exit()
        print('objective retracted')
        self.navigationController.set_z_limit_pos_mm(SOFTWARE_POS_LIMIT.Z_POSITIVE)

        # home XY, set zero and set software limit
        print('home xy')
        timestamp_start = time.time()
        # x needs to be at > + 20 mm when homing y
        self.navigationController.move_x(20) # to-do: add blocking code
        while self.microcontroller.is_busy():
            time.sleep(0.005)
        # home y
        self.navigationController.home_y()
        t0 = time.time()
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 10:
                print('y homing timeout, the program will exit')
                exit()
        self.navigationController.zero_y()
        # home x
        self.navigationController.home_x()
        t0 = time.time()
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 10:
                print('y homing timeout, the program will exit')
                exit()
        self.navigationController.zero_x()
        self.slidePositionController.homing_done = True

        # move to scanning position
        self.navigationController.move_x(20)
        while self.microcontroller.is_busy():
            time.sleep(0.005)
        self.navigationController.move_y(20)
        while self.microcontroller.is_busy():
            time.sleep(0.005)

        # move z
        self.navigationController.move_z_to(DEFAULT_Z_POS_MM)
        # wait for the operation to finish
        t0 = time.time() 
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 5:
                print('z return timeout, the program will exit')
                exit()

        # open the camera
        # camera start streaming
        # self.camera.set_reverse_x(CAMERA_REVERSE_X) # these are not implemented for the cameras in use
        # self.camera.set_reverse_y(CAMERA_REVERSE_Y) # these are not implemented for the cameras in use
        self.camera.set_software_triggered_acquisition() #self.camera.set_continuous_acquisition()
        self.camera.set_callback(self.streamHandler.on_new_frame)
        self.camera.enable_callback()
        # camera
        self.camera.set_callback(self.streamHandler.on_new_frame)


        # set the configuration of class liveController (LED mode, expore time, etc.)
        self.liveController.set_microscope_mode(self.configurationManager.configurations[0])



        # laser autofocus
        if SUPPORT_LASER_AUTOFOCUS:

            # controllers
            self.configurationManager_focus_camera = core.ConfigurationManager(filename='./focus_camera_configurations.xml')
            self.streamHandler_focus_camera = core.StreamHandler()
            self.liveController_focus_camera = core.LiveController(self.camera_focus,self.microcontroller,self.configurationManager_focus_camera,control_illumination=False,for_displacement_measurement=True)
            self.multipointController = core.MultiPointController(self.camera,self.navigationController,self.liveController,self.autofocusController,self.configurationManager,scanCoordinates=self.scanCoordinates,parent=self)
            
            self.displacementMeasurementController = core_displacement_measurement.DisplacementMeasurementController()
            self.laserAutofocusController = core.LaserAutofocusController(self.microcontroller,self.camera_focus,self.liveController_focus_camera,self.navigationController,has_two_interfaces=HAS_TWO_INTERFACES,use_glass_top=USE_GLASS_TOP)

            # camera
            self.camera_focus.set_software_triggered_acquisition() #self.camera.set_continuous_acquisition()
            self.camera_focus.set_callback(self.streamHandler_focus_camera.on_new_frame)
            self.camera_focus.enable_callback()
            self.camera_focus.start_streaming()
        



    def closeEvent(self, event):

        # move the objective to a defined position upon exit
        self.navigationController.move_x(0.1) # temporary bug fix - move_x needs to be called before move_x_to if the stage has been moved by the joystick
        while self.microcontroller.is_busy():
            time.sleep(0.005)
        self.navigationController.move_x_to(30)
        while self.microcontroller.is_busy():
            time.sleep(0.005)
        self.navigationController.move_y(0.1) # temporary bug fix - move_y needs to be called before move_y_to if the stage has been moved by the joystick
        while self.microcontroller.is_busy():
            time.sleep(0.005)
        self.navigationController.move_y_to(30)
        while self.microcontroller.is_busy():
            time.sleep(0.005)

        self.liveController.stop_live()
        self.camera.close()
        self.imageSaver.close()
        self.imageDisplay.close()
        if SUPPORT_LASER_AUTOFOCUS:
            self.camera_focus.close()
            #self.imageDisplayWindow_focus.close()
        self.microcontroller.close()





class AsyncioThread(QThread):
    started = pyqtSignal()

    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.started.emit()
        self.loop.run_forever()


squidController= SquidController(is_simulation=True)
#navigationController = squidController.navigationController

def gray_to_rgb(gray_img):
    # Add a third dimension to the gray image
    if len(gray_img.shape) == 2:
        gray_img = gray_img[:, :, np.newaxis]

    # Convert the gray image to a 3-channel RGB image
    rgb_img = np.repeat(gray_img, 3, axis=2)
    return rgb_img

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self):
        super().__init__()  # don't forget this!
        self.count = 0


    async def recv(self):
        squidController.camera.send_trigger()
        gray_img = squidController.camera.read_frame()
        rgb_img = gray_to_rgb(gray_img)


        # Create the video frame
        new_frame = VideoFrame.from_ndarray(rgb_img, format="bgr24")

        new_frame.pts = self.count # frame.pts
        self.count+=1
        new_frame.time_base = fractions.Fraction(1, 1000)
        await asyncio.sleep(1)
        return new_frame

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
    
    # print("Workspace: ", workspace, "Token:", await server.generate_token({"expires_in": 3600*24*100}))
    
    async def on_init(peer_connection):
        @peer_connection.on("track")
        def on_track(track):
            print(f"Track {track.kind} received")
            peer_connection.addTrack(
                VideoTransformTrack()
            )
            @track.on("ended")
            async def on_ended():
                print(f"Track {track.kind} ended")



    def move_distance(x,y,z, context=None):
        squidController.navigationController.move_x(x)
        squidController.navigationController.move_y(y)
        squidController.navigationController.move_z(z)
        print(f'The stage moved ({x},{y},{z})mm through x,y,z axis')
    
    def snap(context=None):
        squidController.camera.send_trigger()
        gray_img = squidController.camera.read_frame()
        rgb_img = gray_to_rgb(gray_img)
        return rgb_img

            
    def move_stage_to(x,y,z, context=None):
        squidController.navigationController.move_x_to(x)
        squidController.navigationController.move_y_to(y)
        squidController.navigationController.move_z_to(z)
        print(f'The stage moved to position ({x},{y},{z})mm')

        
    await server.register_service(
        {
            "id": "microscope-control-squid",
            "config":{
                "visibility": "public",
                "run_in_executor": True,
                "require_context": True,   
            },
            "type": "echo",
            "move": move_distance,
            "snap": snap
            
        }
    )
    
    await register_rtc_service(
        server,
        service_id=service_id,
        config={
            "visibility": "public",
            # "ice_servers": ice_servers,
            "on_init": on_init,
        },
    )
    

    print(
        f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
    )
    print(f"You can access the webrtc stream at https://aicell-lab.github.io/reef-webrtc/?service_id={service_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC demo for video streaming"
    )
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
    loop.run_forever()
