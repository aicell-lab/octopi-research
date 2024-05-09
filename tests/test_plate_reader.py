import os 
# app specific libraries
import squid_control.control.camera as camera
import squid_control.control.core_reef as core
import squid_control.control.microcontroller as microcontroller
from squid_control.control._def import *
import logging
import squid_control.control.serial_peripherals as serial_peripherals

if SUPPORT_LASER_AUTOFOCUS:
    import squid_control.control.core_displacement_measurement as core_displacement_measurement

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
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions

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

        self.configurationManager = core.ConfigurationManager(filename='./squid_control/channel_configurations.xml')

        self.streamHandler = core.StreamHandler(display_resolution_scaling=DEFAULT_DISPLAY_CROP/100)
        self.liveController = core.LiveController(self.camera,self.microcontroller,self.configurationManager)
        self.navigationController = core.NavigationController(self.microcontroller)
        self.slidePositionController = core.SlidePositionController(self.navigationController,self.liveController,is_for_wellplate=True)
        self.autofocusController = core.AutoFocusController(self.camera,self.navigationController,self.liveController)
        self.scanCoordinates = core.ScanCoordinates()
        self.multipointController = core.MultiPointController(self.camera,self.navigationController,self.liveController,self.autofocusController,self.configurationManager,scanCoordinates=self.scanCoordinates,parent=self)

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
            self.configurationManager_focus_camera = core.ConfigurationManager(filename='./squid_control/focus_camera_configurations.xml')
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

        #self.channel_names =['BF LED matrix full','Fluorescence 405 nm Ex']
    


    def plate_scan(self,well_plate_type='12', illuminate_channels=['BF LED matrix full'], do_autofocus=True, action_ID='testPlateScan'):
        # start the acquisition loop
        self.move_to_scaning_position()
        location_list = self.multipointController.get_location_list(well_plate_type=well_plate_type)
        self.multipointController.set_base_path(DEFAULT_SAVING_PATH)
        self.multipointController.set_selected_configurations(illuminate_channels)
        self.multipointController.do_autofocus = do_autofocus
        self.autofocusController.set_deltaZ(self.autofocusController.deltaZ_usteps)
        self.multipointController.start_new_experiment(action_ID)
        self.multipointController.run_acquisition_reef(location_list=location_list)
        
    def move_to_scaning_position(self):
        
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

    def close(self):
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
        if SUPPORT_LASER_AUTOFOCUS:
            self.camera_focus.close()
        self.microcontroller.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation", help="Ru with simulated hardware.", action = 'store_true')
    args = parser.parse_args()

    #squid = SquidController(is_simulation = args.simulation)
    squid = SquidController(is_simulation = True)
    
    squid.plate_scan(well_plate_type='12')
    squid.close()
