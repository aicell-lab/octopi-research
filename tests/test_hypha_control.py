import pytest
from imjoy_rpc.hypha import connect_to_server

@pytest.mark.asyncio
async def test_squid_service(server_url="https://ai.imjoy.io"):
    SERVER_URL = server_url
    squid_server = await connect_to_server({"server_url": SERVER_URL})
    public_services = await squid_server.list_services("public")
    
    # Example assertion - modify according to actual expected outcome
    assert "squid-control" in public_services, "squid-control service not found in public services"
