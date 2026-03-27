#!/usr/bin/env python3
"""
Entrypoint for nanobot Docker deployment.

Resolves environment variables into the config at runtime, then launches nanobot gateway.
"""

import json
import os
import sys
from pathlib import Path


def resolve_config():
    """Resolve environment variables and write the runtime config."""
    # Paths
    config_path = Path(__file__).parent / "config.json"
    workspace_path = Path(__file__).parent / "workspace"
    resolved_path = Path(__file__).parent / "config.resolved.json"

    # Load base config
    with open(config_path) as f:
        config = json.load(f)

    # Resolve provider API key and base URL from environment
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL", "")
    llm_api_model = os.environ.get("LLM_API_MODEL", "coder-model")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url

    # Resolve agent model
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Resolve gateway host/port
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS", "0.0.0.0")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "18790")
    config["gateway"]["host"] = gateway_host
    config["gateway"]["port"] = int(gateway_port)

    # Resolve webchat channel config
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "8765")
    if "channels" not in config:
        config["channels"] = {}
    config["channels"]["webchat"] = {
        "enabled": True,
        "host": "0.0.0.0",
        "port": int(webchat_port),
        "access_key": os.environ.get("NANOBOT_ACCESS_KEY", ""),
        "allow_from": ["*"],
    }

    # Resolve MCP server environment variables
    mcp_servers = config.get("tools", {}).get("mcpServers", {})
    if "lms" in mcp_servers:
        lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
        lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY", "")
        if lms_backend_url:
            mcp_servers["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        if lms_api_key:
            mcp_servers["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    return str(resolved_path), str(workspace_path)


def main():
    """Main entry point."""
    resolved_config, workspace = resolve_config()

    # Launch nanobot gateway
    os.execvp("nanobot", ["nanobot", "gateway", "--config", resolved_config, "--workspace", workspace])


if __name__ == "__main__":
    main()
