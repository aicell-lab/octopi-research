import uuid
import mimetypes
from urllib.parse import parse_qs
import asyncio

class HyphaDataStore:
    def __init__(self):
        self.storage = {}
        self._svc = None
        self._server = None

    async def setup(self, server, service_id="data-store", visibility="public"):
        self._server = server
        self._svc = await server.register_service({
            "id": service_id,
            "type": "functions",
            "config": {
              "visibility": visibility,
              "require_context": False
            },
            "get": self.http_get,
        }, overwrite=True)

    def get_url(self, obj_id: str):
        assert self._svc, "Service not initialized, call `setup()`"
        assert obj_id in self.storage, "Object not found " + obj_id
        return f"{self._server.config.public_base_url}/{self._server.config.workspace}/apps/{self._svc.id.split(':')[1]}/get?id={obj_id}"

    def put(self, obj_type: str, value: any, name: str, comment: str = ""):
        assert self._svc, "Please call `setup()` before using the store"
        obj_id = str(uuid.uuid4())
        if obj_type == 'file':
            data = value
            assert isinstance(data, (str, bytes)), "Value must be a string or bytes"
            if isinstance(data, str) and data.startswith("file://"):
                # Process file path
                with open(data.replace("file://", ""), 'rb') as fil:
                    data = fil.read()
            mime_type, _ = mimetypes.guess_type(name)
            self.storage[obj_id] = {
                'type': obj_type,
                'name': name,
                'value': data,
                'mime_type': mime_type or 'application/octet-stream',
                'comment': comment
            }
        else:
            self.storage[obj_id] = {
                'type': obj_type,
                'name': name,
                'value': value,
                'mime_type': 'application/json',
                'comment': comment
            }
        return obj_id

    def http_get(self, scope, context=None):
        query_string = scope['query_string']
        id = parse_qs(query_string).get('id', [])[0]
        obj = self.storage.get(id)
        if obj is None:
            return {'status': 404, 'headers': {}, 'body': "Not found: " + id}

        headers = {
            'Content-Type': obj['mime_type'],
            'Content-Length': str(len(obj['value'])),
            'Content-Disposition': f'inline; filename="{obj["name"].split("/")[-1]}"'
        }
        return {
            'status': 200,
            'headers': headers,
            'body': obj['value']
        }