"""
OmniEarth Model Context Protocol (MCP) Server
=============================================
Zero-dependency stdio JSON-RPC 2.0 MCP server exposing OmniEarth's 14 Earth
Observation and environmental data modalities, time-series extraction, and
radiometric index computation to AI coding agents and desktop assistants.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, TextIO

import omniearth
from omniearth.client import OmniEarth
from omniearth.config import config

MCP_PROTOCOL_VERSION = "2024-11-05"

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "omniearth_info",
        "description": "Return OmniEarth version, supported categories, default output directory, and credential health (no secrets).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "omniearth_categories",
        "description": "List all 14 supported OmniEarth satellite, hyperspectral, weather, soil, and environmental data modalities.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "omniearth_search",
        "description": (
            "Search for open Earth Observation scenes or environmental records across 14 modalities "
            "(optical, sar, hyperspectral, elevation, landcover, weather, soil, atmosphere, fire, ocean, "
            "altimetry, precipitation, hydrology, nightlights). 12 modalities require zero credentials."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Data modality name (e.g. optical, sar, hyperspectral, elevation, landcover, weather, soil, atmosphere, fire, ocean, altimetry, precipitation, hydrology, nightlights).",
                },
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "Bounding box [min_lon, min_lat, max_lon, max_lat] in WGS84.",
                },
                "point": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 3,
                    "description": "Point query [lon, lat] or [lon, lat, radius_km].",
                },
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."},
                "year": {"type": "integer", "description": "Single-year filter (YYYY)."},
                "max_cloud_cover": {"type": "number", "description": "Maximum cloud cover percentage (0-100)."},
                "provider": {"type": "string", "description": "Optional specific provider (e.g. dlr_enmap, nasa_emit, cdse)."},
                "dataset": {"type": "string", "description": "Optional dataset selector (e.g. copernicus, srtm, alos)."},
                "limit": {"type": "integer", "default": 5, "description": "Maximum items to return (default: 5)."},
            },
            "required": ["category"],
        },
    },
    {
        "name": "omniearth_timeseries",
        "description": "Extract chronological time-series observations (weather, atmosphere, satellite overpasses) for an AOI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Data modality name."},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "Bounding box [min_lon, min_lat, max_lon, max_lat].",
                },
                "point": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 3,
                    "description": "Point query [lon, lat] or [lon, lat, radius_km].",
                },
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)."},
                "max_cloud_cover": {"type": "number", "description": "Maximum cloud cover percentage."},
                "limit": {"type": "integer", "default": 20, "description": "Maximum records (default: 20)."},
            },
            "required": ["category"],
        },
    },
    {
        "name": "omniearth_compute_index",
        "description": "Compute remote sensing spectral indices (ndvi, ndwi, ndre, evi, nbr, savi, msavi, bsi, mndwi).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {"type": "string", "description": "Spectral index name."},
                "nir": {"description": "NIR band value or numeric list."},
                "red": {"description": "Red band value or numeric list."},
                "green": {"description": "Green band value or numeric list."},
                "blue": {"description": "Blue band value or numeric list."},
                "rededge": {"description": "RedEdge band value or numeric list."},
                "swir": {"description": "SWIR band value or numeric list."},
                "l_factor": {"type": "number", "default": 0.5, "description": "SAVI soil factor L (default: 0.5)."},
            },
            "required": ["index", "nir"],
        },
    },
]


class OmniEarthMCPServer:
    """Stateless JSON-RPC 2.0 handler for OmniEarth MCP tools."""

    def __init__(self, client: Optional[OmniEarth] = None):
        self.client = client or OmniEarth()

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "omniearth_info":
            dlr_u, dlr_p = config.dlr_credentials
            nasa_u, nasa_p = config.earthdata_credentials
            cdse_u, cdse_p = config.cdse_credentials
            payload: Any = {
                "version": omniearth.__version__,
                "categories": self.client.list_categories(),
                "default_outdir": config.default_outdir,
                "credentials_configured": {
                    "dlr_enmap": bool(dlr_u and dlr_p),
                    "nasa_earthdata": bool(nasa_u and nasa_p),
                    "copernicus_cdse": bool(cdse_u and cdse_p),
                },
            }
        elif name == "omniearth_categories":
            payload = {"categories": self.client.list_categories()}
        elif name == "omniearth_search":
            self.client.clear_warnings()
            point_arg = tuple(arguments["point"]) if arguments.get("point") else None
            results = self.client.search(
                category=arguments["category"],
                bbox=arguments.get("bbox"),
                point=point_arg,
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                year=arguments.get("year"),
                max_cloud_cover=arguments.get("max_cloud_cover"),
                provider=arguments.get("provider"),
                dataset=arguments.get("dataset"),
                limit=int(arguments.get("limit", 5)),
            )
            payload = {
                "count": len(results),
                "warnings": self.client.get_warnings(),
                "results": [r.to_dict() for r in results],
            }
        elif name == "omniearth_timeseries":
            self.client.clear_warnings()
            point_arg = tuple(arguments["point"]) if arguments.get("point") else None
            series = self.client.get_time_series(
                category=arguments["category"],
                bbox=arguments.get("bbox"),
                point=point_arg,
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                max_cloud_cover=arguments.get("max_cloud_cover"),
                limit=int(arguments.get("limit", 20)),
            )
            payload = {
                "count": len(series),
                "warnings": self.client.get_warnings(),
                "series": series,
            }
        elif name == "omniearth_compute_index":
            payload = self.client.compute_index(
                index_name=arguments["index"],
                nir=arguments["nir"],
                red=arguments.get("red"),
                green=arguments.get("green"),
                blue=arguments.get("blue"),
                rededge=arguments.get("rededge"),
                swir=arguments.get("swir"),
                l_factor=float(arguments.get("l_factor", 0.5)),
            )
        else:
            raise KeyError(f"Unknown tool: {name}")

        return {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}],
            "isError": False,
        }

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC 2.0 message and return a response dict (or None for notifications)."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params") or {}

        if method.startswith("notifications/"):
            return None

        if method == "initialize":
            result: Any = {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "omniearth-mcp",
                    "version": omniearth.__version__,
                },
            }
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

        if method == "tools/call":
            tool_name = params.get("name")
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Missing required parameter: name"},
                }
            arguments = params.get("arguments") or {}
            try:
                tool_result = self._call_tool(tool_name, arguments)
                return {"jsonrpc": "2.0", "id": req_id, "result": tool_result}
            except KeyError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": str(exc)},
                }
            except Exception as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def run_stdio(
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    server: Optional[OmniEarthMCPServer] = None,
) -> None:
    """Run the newline-delimited JSON-RPC 2.0 MCP server over stdio."""
    in_stream = stdin or sys.stdin
    out_stream = stdout or sys.stdout
    mcp_server = server or OmniEarthMCPServer()

    for raw_line in in_stream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            resp: Optional[Dict[str, Any]] = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
        else:
            resp = mcp_server.handle_request(payload)

        if resp is not None:
            out_stream.write(json.dumps(resp, default=str) + "\n")
            out_stream.flush()


def main() -> None:
    """Entry point for the `omniearth-mcp` CLI command."""
    run_stdio()
