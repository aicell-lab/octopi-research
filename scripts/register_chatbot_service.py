import asyncio
from imjoy_rpc.hypha import connect_to_server, login

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
        }
    }

def move_to_position(config):
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
    squid_svc.move_to_position(config["x"], config["y"], config["z"])
    return {"result": "Moved the stage!"}

def move_by_distance(config):
    print("Moving the stage by distance:", config)
    if config["x"] is None:
        config["x"] = 0
    if config["y"] is None:
        config["y"] = 0
    if config["z"] is None:
        config["z"] = 0
    squid_svc.move_by_distance(config["x"], config["y"], config["z"])
    return {"result": "Moved the stage!"}

async def auto_focus(config):
    squid_svc.auto_focus()
    return {"result": "Auto focused!"}
async def snap_image(config):
    squid_image_url = await squid_svc.snap()
    resp = f"![Image]({squid_image_url})"
    return resp

async def setup():
    global squid_svc
    squid_server = await connect_to_server({"server_url": "https://ai.imjoy.io/"})
    squid_svc = await squid_server.get_service("microscope-control-squid")
    chatbot_extension = {
        "_rintf": True,
        "id": "squid-control",
        "type": "bioimageio-chatbot-extension",
        "name": "Squid Microscope Control",
        "description": "You are a chatbot majoring a microscope. Your mission is answering the user's questions, and also controlling the microscope according to the user's commands. Remember, you are controlling a real microscope, distinguish the questions and commands, and execute them correctly.",
        "get_schema": get_schema,
        "tools": {
            "move_by_distance": move_by_distance,
            "move_to_position": move_to_position, 
            "auto_focus": auto_focus, 
            "snap_image": snap_image,
        }
    }


    server_url = "https://chat.bioimage.io"
    token = await login({"server_url": server_url})
    server = await connect_to_server({"server_url": server_url, "token": token})
    svc = await server.register_service(chatbot_extension)
    print(f"Extension service registered with id: {svc.id}, you can visit the service at: https://bioimage.io/chat?server={server_url}&extension={svc.id}")

if __name__ == "__main__":
   loop = asyncio.get_event_loop()
   loop.create_task(setup())
   loop.run_forever()