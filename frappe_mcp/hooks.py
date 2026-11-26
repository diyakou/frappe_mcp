app_name = "frappe_mcp"
app_title = "Frappe MCP"
app_publisher = "ClickERP"
app_description = "MCP server endpoint for Frappe v15 — per-user session auth"
app_license = "MIT"
# DocTypes bundled with the app
doc_types = [
    {"doctype": "MCP Call Log", "module": "Frappe MCP", "json": "frappe_mcp/frappe_mcp/doctype/mcp_call_log/mcp_call_log.json"},
]
