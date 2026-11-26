"""Stdio MCP adapter — bridges an MCP client (Claude Desktop / opencode) to the
Frappe MCP endpoint at dev-erp.clickapps.ir. Login happens on first tool call.

Env:
  FRAPPE_URL  (default https://erp.clickapps.ir)
  FRAPPE_USER, FRAPPE_PASSWORD   — or pass login via the `login` tool
"""
import json
import os
import sys

import requests

URL = os.environ.get("FRAPPE_URL", "https://dev-erp.clickapps.ir").rstrip("/")
ENDPOINT = f"{URL}/api/method/frappe_mcp.mcp.handle"
LOGIN = f"{URL}/api/method/login"

session = requests.Session()
TOOLS = [
    {"name": "login", "description": "Log in with your Frappe username and password.",
     "inputSchema": {"type": "object", "properties": {
         "usr": {"type": "string"}, "pwd": {"type": "string"}},
         "required": ["usr", "pwd"]}},
    {"name": "search_doctypes", "description": "Find DocTypes by name.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]}},
    {"name": "get_doctype_schema", "description": "Get fields of a DocType.",
     "inputSchema": {"type": "object", "properties": {"doctype": {"type": "string"}},
                     "required": ["doctype"]}},
    {"name": "list_documents", "description": "List documents with filters (honors permissions).",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "filters": {"type": "object"},
         "fields": {"type": "array", "items": {"type": "string"}},
         "limit": {"type": "integer"}}, "required": ["doctype"]}},
    {"name": "get_document", "description": "Read one document.",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "name": {"type": "string"}},
         "required": ["doctype", "name"]}},
    {"name": "count_documents", "description": "Count matching documents.",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "filters": {"type": "object"}},
         "required": ["doctype"]}},
    {"name": "create_document", "description": "Create a document.",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "data": {"type": "object"}},
         "required": ["doctype", "data"]}},
    {"name": "update_document", "description": "Update a document.",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "name": {"type": "string"},
         "data": {"type": "object"}}, "required": ["doctype", "name", "data"]}},
    {"name": "delete_document", "description": "Delete a document.",
     "inputSchema": {"type": "object", "properties": {
         "doctype": {"type": "string"}, "name": {"type": "string"}},
         "required": ["doctype", "name"]}},
    {"name": "call_method", "description": "Call a whitelisted server method.",
     "inputSchema": {"type": "object", "properties": {
         "method": {"type": "string"}, "args": {"type": "object"}},
         "required": ["method"]}},
    {"name": "run_report", "description": "Run a Frappe report.",
     "inputSchema": {"type": "object", "properties": {
         "report": {"type": "string"}, "filters": {"type": "object"}},
         "required": ["report"]}},
]


def rpc(method, params=None, id=1):
    body = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        body["params"] = params
    r = session.post(ENDPOINT, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", str(data["error"])))
    return data.get("result")


def do_login(usr, pwd):
    r = session.post(LOGIN, data={"usr": usr, "pwd": pwd}, timeout=30)
    r.raise_for_status()
    return f"Logged in as {usr}"


def call_tool(name, args):
    if name == "login":
        return do_login(args["usr"], args["pwd"])
    # auto-login from env on first call
    if not os.environ.get("_LOGGED") and os.environ.get("FRAPPE_USER"):
        do_login(os.environ["FRAPPE_USER"], os.environ.get("FRAPPE_PASSWORD", ""))
        os.environ["_LOGGED"] = "1"
    out = rpc("tools/call", {"name": name, "arguments": args}, id=2)
    return out


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, id = req.get("method"), req.get("id")
        params = req.get("params") or {}
        try:
            if method == "initialize":
                result = {"protocolVersion": "2025-06-18",
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "frappe-mcp-adapter", "version": "0.1.0"}}
            elif method == "notifications/initialized" or id is None:
                continue
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                out = call_tool(params["name"], params.get("arguments") or {})
                result = {"content": [{"type": "text",
                                       "text": json.dumps(out, default=str, ensure_ascii=False)}]}
            else:
                raise RuntimeError(f"Method not found: {method}")
            resp = {"jsonrpc": "2.0", "id": id, "result": result}
        except Exception as e:
            resp = {"jsonrpc": "2.0", "id": id,
                    "result": {"content": [{"type": "text", "text": str(e)}], "isError": True}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
