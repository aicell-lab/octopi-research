import pytest
from imjoy_rpc.hypha import login, connect_to_server

@pytest.mark.asyncio
async def test_squid_service(server_url="https://ai.imjoy.io"):
      SERVER_URL = server_url
      squid_server = await connect_to_server(
      {"server_url": SERVER_URL}
      )
      squid_svc = await squid_server.get_service("squid-control")
      public_services = await squid_server.list_services("public")
      print(public_services)


