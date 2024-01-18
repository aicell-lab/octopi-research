# set QT_API environment variable
import os 
import argparse
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

# app specific libraries
import squid_control.control.gui_hcs as gui

from configparser import ConfigParser
from squid_control.control.widgets import ConfigEditorBackwardsCompatible, ConfigEditorForAcquisitions
import glob

parser = argparse.ArgumentParser()
parser.add_argument("--simulation", help="Run the GUI with simulated hardware.", action = 'store_true')
args = parser.parse_args()

def show_config(cfp, configpath, main_gui):
    config_widget = ConfigEditorBackwardsCompatible(cfp, configpath, main_gui)
    config_widget.exec_()

def show_acq_config(cfm):
    acq_config_widget = ConfigEditorForAcquisitions(cfm)
    acq_config_widget.exec_()

if __name__ == "__main__":
    legacy_config = False
    cf_editor_parser = ConfigParser()
    #config_files = glob.glob('.' + '/' + 'configuration*.ini')
    try:
        # Attempt to find .ini files using the original method
        config_files = glob.glob('.' + '/' + 'configuration*.ini')
        if not config_files:
            # If no .ini files are found using the original method, fall back to the alternative method
            raise FileNotFoundError
    except FileNotFoundError:
        # Get the current directory of the script
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # Search for .ini files in the current directory
        config_files = glob.glob(os.path.join(current_directory, 'control/*.ini'))
    if config_files:
        if len(config_files) > 1:
            print('multiple machine configuration files found, the program will exit')
            exit()
        cf_editor_parser.read(config_files[0])
    else:
        print('configuration*.ini file not found, defaulting to legacy configuration')
        legacy_config = True
    app = QApplication([])
    app.setStyle('Fusion')
    if(args.simulation):
        win = gui.OctopiGUI(is_simulation = True)
    else:
        win = gui.OctopiGUI()
       
    acq_config_action = QAction("Acquisition Settings", win)
    acq_config_action.triggered.connect(lambda : show_acq_config(win.configurationManager))

    file_menu = QMenu("File", win)
    file_menu.addAction(acq_config_action)

    if not legacy_config:
        config_action = QAction("Microscope Settings", win)
        config_action.triggered.connect(lambda : show_config(cf_editor_parser, config_files[0], win))
        file_menu.addAction(config_action)
    
    menu_bar = win.menuBar()
    menu_bar.addMenu(file_menu)
    win.show()
    app.exec_() #sys.exit(app.exec_())
