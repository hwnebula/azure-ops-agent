"""Stretch goal: expose ``tools.build_tools()`` as an MCP server.

Each ToolSpec already has a name, description, and JSON input schema, so the server is a thin
adapter: list_tools returns the specs, and call_tool returns
``ToolSpec.invoke(...).to_model_payload()``.
"""
