import io
import json
import sys
from unittest.mock import MagicMock

from omniearth.mcp_server import OmniEarthMCPServer, MCP_PROTOCOL_VERSION, main, run_stdio
from omniearth.models import Asset, Category, SearchResult, SearchResults


def test_mcp_lifecycle_and_errors():
    client = MagicMock()
    server = OmniEarthMCPServer(client=client)

    init_resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_resp["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert init_resp["result"]["serverInfo"]["name"] == "omniearth-mcp"

    assert server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    ping_resp = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping_resp["result"] == {}

    list_resp = server.handle_request({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    tool_names = [t["name"] for t in list_resp["result"]["tools"]]
    assert "omniearth_search" in tool_names
    assert "omniearth_compute_index" in tool_names

    missing_name = server.handle_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {}})
    assert missing_name["error"]["code"] == -32602

    unknown_tool = server.handle_request({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "no_such_tool", "arguments": {}},
    })
    assert unknown_tool["error"]["code"] == -32602

    unknown_method = server.handle_request({"jsonrpc": "2.0", "id": 6, "method": "unknown/method"})
    assert unknown_method["error"]["code"] == -32601


def test_mcp_tool_calls_and_runtime_exception():
    client = MagicMock()
    client.list_categories.return_value = ["optical", "weather"]
    client.get_warnings.return_value = []
    client.search.return_value = SearchResults([
        SearchResult(
            id="S2A_1",
            collection="sentinel-2-l2a",
            category=Category.OPTICAL,
            provider="aws",
            assets={"visual": Asset(key="visual", href="https://example.com/v.tif")},
        )
    ])
    client.get_time_series.return_value = [{"datetime": "2026-01-01", "temp": 25.0}]
    client.compute_index.return_value = {"index": "ndvi", "values": 0.6}

    server = OmniEarthMCPServer(client=client)

    info_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "omniearth_info", "arguments": {}},
    })
    info_data = json.loads(info_resp["result"]["content"][0]["text"])
    assert "credentials_configured" in info_data

    cats_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {"name": "omniearth_categories", "arguments": {}},
    })
    assert json.loads(cats_resp["result"]["content"][0]["text"])["categories"] == ["optical", "weather"]

    search_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "omniearth_search",
            "arguments": {"category": "optical", "point": [78.5, 20.6, 5.0], "limit": 2},
        },
    })
    search_data = json.loads(search_resp["result"]["content"][0]["text"])
    assert search_data["count"] == 1
    assert search_data["results"][0]["id"] == "S2A_1"

    ts_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
            "name": "omniearth_timeseries",
            "arguments": {"category": "weather", "bbox": [78.5, 20.6, 78.6, 20.7]},
        },
    })
    assert json.loads(ts_resp["result"]["content"][0]["text"])["count"] == 1

    idx_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
            "name": "omniearth_compute_index",
            "arguments": {"index": "ndvi", "nir": 0.8, "red": 0.2},
        },
    })
    assert json.loads(idx_resp["result"]["content"][0]["text"])["values"] == 0.6

    client.search.side_effect = RuntimeError("Upstream down")
    err_resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/call",
        "params": {"name": "omniearth_search", "arguments": {"category": "optical"}},
    })
    assert err_resp["result"]["isError"] is True
    assert "Upstream down" in err_resp["result"]["content"][0]["text"]


def test_mcp_run_stdio_and_main(monkeypatch):
    client = MagicMock()
    server = OmniEarthMCPServer(client=client)

    stdin = io.StringIO(
        "\n"
        "{bad json\n"
        + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n"
        + json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    )
    stdout = io.StringIO()
    run_stdio(stdin=stdin, stdout=stdout, server=server)

    lines = [json.loads(line) for line in stdout.getvalue().strip().splitlines()]
    assert len(lines) == 2
    assert lines[0]["error"]["code"] == -32700
    assert lines[1]["id"] == 1
    assert lines[1]["result"] == {}

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "ping"}) + "\n"))
    cap_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", cap_out)
    main()
    assert json.loads(cap_out.getvalue().strip())["id"] == 9
