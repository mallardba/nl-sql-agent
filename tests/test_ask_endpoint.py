import pytest


@pytest.mark.asyncio
async def test_ask_endpoint_if_present(client):
    ping = await client.options("/ask")
    if ping.status_code in (404, 405):
        pytest.skip("/ask endpoint not available in this build")
    r = await client.post("/ask", json={"question": "sales by month last 6 months"})
    assert r.status_code == 200
    data = r.json()
    assert "sql" in data
    assert "rows" in data and isinstance(data["rows"], list)
