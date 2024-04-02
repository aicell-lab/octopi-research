import asyncio
from imjoy import api
import numpy as np

async def setup():
    # Use micropip to install pydantic asynchronously
    import micropip
    await micropip.install("pydantic")

    # Now that pydantic is installed, we can safely import it
    from pydantic import BaseModel, Field

    class MoveByDistanceInput(BaseModel):
        """Move the stage by a specified distance, the unit of distance is millimeters, so you need to input the distance in millimeters."""
        x: float = Field(description="Move the stage along X axis.")
        y: float = Field(description="Move the stage along Y axis.")
        z: float = Field(description="Move the stage along Z axis.")

    class SnapImageInput(BaseModel):
        """Snap an image from microscope."""
        exposure: int = Field(description="Set the microscope camera's exposure time. and the time unit is ms, so you need to input the time in miliseconds.")
    

    def move_stage_by_distance(kwargs):
        config = MoveByDistanceInput(**kwargs)
        squid_svc.move_by_distance(config.x, config.y, config.z)
        print(config.x, config.y, config.z)
        return "Moved the stage!"

    def snap_image(kwargs):
        config = SnapImageInput(**kwargs)
        squid_image = squid_svc.snap()
        viewer = api.createWindow(type="itk-vtk-viewer", src="https://kitware.github.io/itk-vtk-viewer/app")
        viewer.setImage(squid_image)
        return "Here is the image"

    global squid_svc
    from imjoy_rpc.hypha import connect_to_server
    squid_server = await connect_to_server({"server_url": "https://ai.imjoy.io/"})
    squid_svc = await squid_server.get_service("microscope-control-squid")
    print(squid_svc)

    chatbot = api.createWindow(src="https://chat.bioimage.io/public/apps/bioimageio-chatbot-client/chat")

    def get_schema():
        return {
            "move_by_distance": MoveByDistanceInput.schema(),
            "snap_image": SnapImageInput.schema()
        }

    extension = {
        "_rintf": True,
        "type": "bioimageio-chatbot-extension",
        "id": "squid-control",
        "name": "Squid Microscope Control",
        "description": "Control the microscope based on the user's request. Now you can move the microscope stage, and snap an image.",
        "get_schema": get_schema,
        "tools": {
            "move_by_distance": move_stage_by_distance,
            "snap_image": snap_image,
        }
    }
    await chatbot.registerExtension(extension)
    print('registered')

api.export({"setup": setup})