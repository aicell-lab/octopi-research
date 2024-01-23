## Setting up the environments

### install Squid software dependencies
```
sudo rm /var/lib/apt/lists/lock
sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install python3-pyqtgraph
sudo apt-get install python3-pyqt5
sudo apt-get install git
git clone https://github.com/hongquanli/octopi-research.git
pip3 install qtpy pyserial pandas imageio pyqt5-tools pyqtgraph scipy tensorrt crc==1.3.0
python3 -m pip install --upgrade --user setuptools==58.3.0
pip3 install opencv-python opencv-contrib-python
pip3 install lxml
pip3 install numpy
```

### install camera drivers
If you're using Daheng cameras, follow instructions in the `drivers and libraries/daheng camera` folder

If you're using The Imaging Source cameras, follow instructions on https://github.com/TheImagingSource/tiscamera 

### enable access to serial ports without sudo

```
sudo usermod -aG dialout $USER
```
Reboot the computer for the setting to take effect.