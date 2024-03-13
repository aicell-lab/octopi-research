import asyncio
import os
import json
import datetime
import secrets
import aiofiles
from imjoy_rpc.hypha import login, connect_to_server
from pydantic import BaseModel, Field
from schema_agents.role import Role
from schema_agents.schema import Message
from typing import Dict, List, Optional
import sys
import io
import pkg_resources
from typing import Any, Dict, List, Optional, Union
from io import BytesIO
import imageio
import base64
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import time

def resize_image(image, new_size):
    # Using Pillow to resize the image
    pil_image = Image.fromarray((image * 255).astype('uint8'))  # Assuming image is in the range [0, 1]
    pil_image = pil_image.resize(new_size)
    resized_image = np.array(pil_image) / 255.0  # Convert back to [0, 1] range
    return resized_image



def image_to_markdown(image, new_size=(100, 100)):
    # Resize the image
    resized_image = resize_image(image, new_size)

    # Plot the resized image using matplotlib
    plt.imshow(resized_image)
    plt.axis('off')

    # Save the image to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    plt.close()

    # Encode the resized image to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Create the Markdown string with the encoded image
    markdown_string = f"![Image](data:image/png;base64,{image_base64})"

    return markdown_string





class FinalResponse(BaseModel):
    """The final response to the user's question. If the retrieved context has low relevance score, or the question isn't relevant to the retrieved context, return 'I don't know'."""
    response: str = Field(description="The answer to the user's question in markdown format.")


class UserProfile(BaseModel):
    """The user's profile. This will be used to personalize the response."""
    name: str = Field(description="The user's name.", max_length=32)
    occupation: str = Field(description="The user's occupation. ", max_length=128)
    background: str = Field(description="The user's background. ", max_length=256)

class QuestionWithHistory(BaseModel):
    """The user's question, chat history and user's profile."""
    question: str = Field(description="The user's question.")
    chat_history: Optional[List[Dict[str, str]]] = Field(None, description="The chat history.")
    user_profile: Optional[UserProfile] = Field(None, description="The user's profile. You should use this to personalize the response based on the user's background and occupation.")

class MoveByDistanceAction(BaseModel):
    """Move the stage by a specified distance."""
    x: int = Field(description="Move the stage along X direction (mm).")
    y: int = Field(description="Move the stage along Y direction (mm).")
    z: int = Field(description="Move the stage along Z direction (mm).")

class SnapImageAction(BaseModel):
    """Snap an image from microscope"""
    #path: str = Field(description="File path to save the image. Format should be .tiff")

class ActionPlan(BaseModel):
    """Creat a list of actions according to the user's request."""
    actions: List[Union[MoveByDistanceAction,SnapImageAction]] = Field(description="A list of actions")

async def create_customer_service(): ###Async version####################
    #Initialize squid microscopy access
    squid_server = await connect_to_server({"server_url": "https://ai.imjoy.io/"})

    squid_svc = await squid_server.get_service("microscope-control-squid")

    def clean_image_in_history(chat_history):
        for chat in chat_history:
            string=chat['content']
            index = string.find("![Image]")
        # If the image markdown string is found, update the string
            if index != -1:
                string = string[:index + len("![Image]")]
            chat['content']=string

    async def respond_to_user(question_with_history: QuestionWithHistory = None, role: Role = None) -> str:
        """Answer the user's question directly or retrieve relevant documents from the documentation, or create a Python Script to get information about details of models."""
        #Clean the images in chat history.
        clean_image_in_history(question_with_history.chat_history)
        inputs = [question_with_history.user_profile] + list(question_with_history.chat_history) + [question_with_history.question]
        # The channel info will be inserted at the beginning of the inputs
        req = await role.aask(inputs, Union[FinalResponse,ActionPlan])
        if isinstance(req,ActionPlan):
            return_string=''
            for action in req.actions:

                if isinstance(action, MoveByDistanceAction):

                    await squid_svc.move_by_distance(action.x,action.y,action.z)
                    return_string += f"The stage has moved, distance: ({action.x}, {action.y}, {action.z}) through X, Y and Z axis.\n"
                elif isinstance(action,SnapImageAction):
                    squid_image = await squid_svc.snap()
                    markdown_image=image_to_markdown(squid_image)
                    
                    return_string += f"Here is the image:\n {markdown_image}\n"

            return return_string
        # else:
        #     raise RuntimeError("Unsupported action.")
        
    customer_service = Role(
        name="MicroscopeOperator",
        profile="Microscope Controller",
        goal="Your goal is control the microscope based on the user's request.",
        constraints=None,
        actions=[respond_to_user],
    )
    return customer_service

async def save_chat_history(chat_log_full_path, chat_his_dict):    
    # Serialize the chat history to a json string
    chat_history_json = json.dumps(chat_his_dict)

    # Write the serialized chat history to the json file
    async with aiofiles.open(chat_log_full_path, mode='w', encoding='utf-8') as f:
        await f.write(chat_history_json)

    
async def connect_server(server_url):
    """Connect to the server and register the chat service."""
    login_required = os.environ.get("BIOIMAGEIO_LOGIN_REQUIRED") == "true"
    if login_required:
        token = await login({"server_url": server_url})
    else:
        token = None
    server = await connect_to_server({"server_url": server_url, "token": token, "method_timeout": 100})
    await register_chat_service(server)
    
async def register_chat_service(server):
    """Hypha startup function."""
    login_required = os.environ.get("BIOIMAGEIO_LOGIN_REQUIRED") == "true"

    chat_logs_path = os.environ.get("BIOIMAGEIO_CHAT_LOGS_PATH", "./chat_logs")
    assert chat_logs_path is not None, "Please set the BIOIMAGEIO_CHAT_LOGS_PATH environment variable to the path of the chat logs folder."
    if not os.path.exists(chat_logs_path):
        print(f"The chat session folder is not found at {chat_logs_path}, will create one now.")
        os.makedirs(chat_logs_path, exist_ok=True)
    
    customer_service = await create_customer_service()
    
    event_bus = customer_service.get_event_bus()
    event_bus.register_default_events()
        
    def load_authorized_emails():
        if login_required:
            authorized_users_path = os.environ.get("BIOIMAGEIO_AUTHORIZED_USERS_PATH")
            if authorized_users_path:
                assert os.path.exists(authorized_users_path), f"The authorized users file is not found at {authorized_users_path}"
                with open(authorized_users_path, "r") as f:
                    authorized_users = json.load(f)["users"]
                authorized_emails = [user["email"] for user in authorized_users if "email" in user]
            else:
                authorized_emails = None
        else:
            authorized_emails = None
        return authorized_emails

    authorized_emails = load_authorized_emails()
    def check_permission(user):
        if authorized_emails is None or user["email"] in authorized_emails:
            return True
        else:
            return False
        
    async def report(user_report, context=None):
        if login_required and context and context.get("user"):
            assert check_permission(context.get("user")), "You don't have permission to report the chat history."
        chat_his_dict = {'type':user_report['type'],
                         'feedback':user_report['feedback'],
                         'conversations':user_report['messages'], 
                         'session_id':user_report['session_id'], 
                        'timestamp': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                        'user': context.get('user')}
        session_id = user_report['session_id'] + secrets.token_hex(4)
        filename = f"report-{session_id}.json"
        # Create a chat_log.json file inside the session folder
        chat_log_full_path = os.path.join(chat_logs_path, filename)
        await save_chat_history(chat_log_full_path, chat_his_dict)
        print(f"User report saved to {filename}")
        
    async def chat(text, chat_history, user_profile=None, channel=None, status_callback=None, session_id=None, context=None):
        if login_required and context and context.get("user"):
            assert check_permission(context.get("user")), "You don't have permission to use the chatbot, please sign up and wait for approval"
        session_id = session_id or secrets.token_hex(8)
        # Listen to the `stream` event
        async def stream_callback(message):
            if message.type in ["function_call", "text"]:
                if message.session.id == session_id:
                    await status_callback(message.dict())

        event_bus.on("stream", stream_callback)

        # user_profile = {"name": "lulu", "occupation": "data scientist", "background": "machine learning and AI"}
        m = QuestionWithHistory(question=text, chat_history=chat_history, user_profile=UserProfile.parse_obj(user_profile))
        try:
            response = await customer_service.handle(Message(content=m.json(), data=m , role="User", session_id=session_id))
            # get the content of the last response
            response = response[-1].content
            print(f"\nUser: {text}\nChatbot: {response}")
        except Exception as e:
            event_bus.off("stream", stream_callback)
            raise e
        else:
            event_bus.off("stream", stream_callback)

        if session_id:
            chat_history.append({ 'role': 'user', 'content': text })
            chat_history.append({ 'role': 'assistant', 'content': response })
            chat_his_dict = {'conversations':chat_history, 
                     'timestamp': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                     'user': context.get('user')}
            filename = f"chatlogs-{session_id}.json"
            chat_log_full_path = os.path.join(chat_logs_path, filename)
            await save_chat_history(chat_log_full_path, chat_his_dict)
            print(f"Chat history saved to {filename}")
        return response

    async def ping(context=None):
        if login_required and context and context.get("user"):
            assert check_permission(context.get("user")), "You don't have permission to use the chatbot, please sign up and wait for approval"
        return "pong"

    hypha_service_info = await server.register_service({
        "name": "BioImage.IO Chatbot",
        "id": "bioimageio-chatbot",
        "config": {
            "visibility": "public",
            "require_context": True
        },
        "ping": ping,
        "chat": chat,
        "report": report,
        "channels": []
    })
    
    version = pkg_resources.get_distribution('bioimageio-chatbot').version
    
    with open(os.path.join(os.path.dirname(__file__), "static/index.html"), "r") as f:
        index_html = f.read()
    index_html = index_html.replace("https://ai.imjoy.io", server.config['public_base_url'] or f"http://127.0.0.1:{server.config['port']}")
    index_html = index_html.replace('"bioimageio-chatbot"', f'"{hypha_service_info["id"]}"')
    index_html = index_html.replace('v0.1.0', f'v{version}')
    index_html = index_html.replace("LOGIN_REQUIRED", "true" if login_required else "false")
    async def index(event, context=None):
        return {
            "status": 200,
            "headers": {'Content-Type': 'text/html'},
            "body": index_html
        }
    
    await server.register_service({
        "id": "bioimageio-chatbot-client",
        "type": "functions",
        "config": {
            "visibility": "public",
            "require_context": False
        },
        "index": index,
    })
    server_url = server.config['public_base_url']

    print(f"The BioImage.IO Chatbot is available at: {server_url}/{server.config['workspace']}/apps/bioimageio-chatbot-client/index")

### This is about registering hypha





# if __name__ == "__main__":
#     # asyncio.run(main())
#     server_url = "https://ai.imjoy.io"
#     loop = asyncio.get_event_loop()
#     loop.create_task(connect_server(server_url))
#     loop.run_forever()