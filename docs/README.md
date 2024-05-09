# WebRTC Hypha Demo

This project showcases a WebRTC-based web application designed for remote microscope control, featuring a dynamic and interactive user interface. It leverages the ImJoy platform to enhance control through the use of chatbot plugins. You can see the webpage at: https://aicell-lab.github.io/squid-control/

## Features

- **Microscope Movement Control**: Enables precise manipulation of the microscope's x, y, and z axes via a web interface.
- **WebRTC Integration**: Uses WebRTC for peer-to-peer connections, facilitating real-time video and audio streams.
- **Responsive UI with Bootstrap**: Utilizes Bootstrap for responsive design and Font Awesome for icons.
- **ImJoy Chatbot Plugin Integration**: Allows the loading of external ImJoy plugins, particularly for advanced microscope control via chatbots.
- **Interactive SVG Display**: Shows the microscope stage position dynamically with an SVG.

## Setup

1. **Prerequisites**: A modern web browser that supports HTML5, CSS3, and JavaScript ES6+ is required.
2. **Dependencies**: The application depends on these JavaScript libraries:
   - Bootstrap 4.3.1
   - Font Awesome 5.15.3
   - ImJoy-RPC 0.5.36
   - ImJoy Loader

3. **Starting the Application**: Open `index.html` in your browser to launch the application. If needed, modify the `service-id` in the provided input box to connect to your WebRTC service.

## Usage

- **Control Panel**: The control panel allows you to start or stop the live stream, adjust the microscope's position, toggle the illumination, and start plate scanning.
- **Movement Input**: Input the x, y, and z values to adjust the microscope's movement in millimeters.
- **Chatbot Plugin**: Load custom plugins via the ImJoy interface to expand functionality or connect with an AI-powered chatbot for automated control.

## Extending the Application

Enhance the application by adding new features or integrating more ImJoy plugins. Customize behavior or add new functions by modifying the JavaScript code within the `<script>` tags.

---