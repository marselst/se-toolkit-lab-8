"""Stdio MCP server exposing observability operations as typed tools."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_victorialogs_url: str = ""
_victoriatraces_url: str = ""

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchQuery(BaseModel):
    query: str = Field(
        default="*",
        description="LogsQL query string. Example: 'level:error' or '{service=\"backend\"}'",
    )
    limit: int = Field(default=20, ge=1, le=1000, description="Max log entries to return")
    time_range: str = Field(
        default="1h",
        description="Time range for the query (e.g., '1h', '30m', '24h')",
    )


class _LogsErrorCountQuery(BaseModel):
    time_range: str = Field(
        default="1h",
        description="Time window to count errors (e.g., '1h', '30m', '24h')",
    )


class _TracesListQuery(BaseModel):
    service: str = Field(
        default="",
        description="Service name to filter traces (empty for all services)",
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max traces to return")
    time_range: str = Field(
        default="1h",
        description="Time range for the query (e.g., '1h', '30m', '24h')",
    )


class _TracesGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text(data: Any) -> list[TextContent]:
    """Serialize data to a JSON text block."""
    if isinstance(data, (dict, list)):
        content = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        content = str(data)
    return [TextContent(type="text", text=content)]


async def _victorialogs_request(url: str, params: dict[str, str]) -> Any:
    """Make a request to VictoriaLogs API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        # VictoriaLogs returns newline-delimited JSON
        lines = response.text.strip().split("\n")
        results = []
        for line in lines:
            if line.strip():
                results.append(json.loads(line))
        return results


async def _victoriatraces_request(url: str) -> Any:
    """Make a request to VictoriaTraces API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs using VictoriaLogs."""
    url = f"{_victorialogs_url}/select/logsql/query"
    params = {
        "query": args.query,
        "limit": str(args.limit),
        "time": args.time_range,
    }
    try:
        results = await _victorialogs_request(url, params)
        return _text({"logs": results, "count": len(results)})
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs request failed: {e}"})


async def _logs_error_count(args: _LogsErrorCountQuery) -> list[TextContent]:
    """Count errors per service over a time window."""
    url = f"{_victorialogs_url}/select/logsql/query"
    params = {
        "query": "level:error OR severity:ERROR OR status:5*",
        "limit": "1000",
        "time": args.time_range,
    }
    try:
        results = await _victorialogs_request(url, params)
        # Group by service
        error_counts: dict[str, int] = {}
        for entry in results:
            service = entry.get("service.name", entry.get("service", "unknown"))
            error_counts[service] = error_counts.get(service, 0) + 1
        return _text({"time_range": args.time_range, "errors_by_service": error_counts})
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs request failed: {e}"})


async def _traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces."""
    # VictoriaTraces uses a different API - query via VMUI
    url = f"{_victoriatraces_url}/api/v1/traces"
    params = {"limit": str(args.limit)}
    if args.service:
        params["service"] = args.service
    try:
        results = await _victoriatraces_request(url)
        return _text({"traces": results.get("data", []), "count": len(results.get("data", []))})
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces request failed: {e}"})


async def _traces_get(args: _TracesGetQuery) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    url = f"{_victoriatraces_url}/api/v1/traces/{args.trace_id}"
    try:
        result = await _victoriatraces_request(url)
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces request failed: {e}"})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_Registry = tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]

_TOOLS: dict[str, _Registry] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (
        model,
        handler,
        Tool(name=name, description=description, inputSchema=schema),
    )


_register(
    "obs_logs_search",
    "Search logs in VictoriaLogs using LogsQL. Returns matching log entries.",
    _LogsSearchQuery,
    _logs_search,
)
_register(
    "obs_logs_error_count",
    "Count errors per service over a time window in VictoriaLogs.",
    _LogsErrorCountQuery,
    _logs_error_count,
)
_register(
    "obs_traces_list",
    "List recent traces from VictoriaTraces. Optionally filter by service.",
    _TracesListQuery,
    _traces_list,
)
_register(
    "obs_traces_get",
    "Fetch a specific trace by ID from VictoriaTraces.",
    _TracesGetQuery,
    _traces_get,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    global _victorialogs_url, _victoriatraces_url
    _victorialogs_url = os.environ.get("VICTORIALOGS_URL", "http://localhost:9428")
    _victoriatraces_url = os.environ.get("VICTORIATRACES_URL", "http://localhost:10428")
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
