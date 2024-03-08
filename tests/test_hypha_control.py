from pydantic import BaseModel, Field
from imjoy_rpc import api
    
class MoveStageInput(BaseModel):
    """Move the microscope stage"""
    x: float = Field(..., description="x offset")
    y: float = Field(..., description="y offset")

class SnapImageInput(BaseModel):
    """Move the microscope stage"""
    exposure: float = Field(..., description="exposure time")

def move_stage(kwargs):
    config = MoveStageInput(**kwargs)
    print(config.x, config.y)

    return "success"

def snap_image(kwargs):
    config = SnapImageInput(**kwargs)
    print(config.exposure)

    return "success"

async def setup():
    chatbot = await api.createWindow(src="http://127.0.0.1:9003/public/apps/bioimageio-chatbot-client/chat")
    
    def get_schema():
        return {
            "move_stage": MoveStageInput.schema(),
            "snap_image": SnapImageInput.schema()
        }

    extension = {
        "_rintf": True,
        "id": "squid-control",
        "name": "Squid Microscope Control",
        "description": "Contorl the squid microscope....",
        "get_schema": get_schema,
        "tools": {
            "move_stage": move_stage,
            "snap_image": snap_image,
        }
    }
    await chatbot.registerExtension(extension)

api.export({"setup": setup})