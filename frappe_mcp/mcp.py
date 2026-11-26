"""MCP over HTTP endpoint (JSON-RPC).

Mount: POST <site>/api/method/frappe_mcp.mcp.handle
Auth:  normal Frappe session cookie / token — every tool runs as the logged-in
       user; Frappe applies that user's roles and permissions to all data.
"""
import json

import frappe
from frappe import _

TOOLS = [
    {
        "name": "search_doctypes",
        "description": "Find DocTypes by name (only ones the user can read).",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}},
                        "required": ["query"]},
    },
    {
        "name": "get_doctype_schema",
        "description": "Get fields/labels of a DocType.",
        "inputSchema": {"type": "object", "properties": {"doctype": {"type": "string"}},
                        "required": ["doctype"]},
    },
    {
        "name": "list_documents",
        "description": "List documents of a DocType with filters. Honors user permissions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doctype": {"type": "string"},
                "filters": {"type": "object"},
                "fields": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 20},
                "order_by": {"type": "string"},
            },
            "required": ["doctype"],
        },
    },
    {
        "name": "get_document",
        "description": "Read one document (and permitted child rows).",
        "inputSchema": {"type": "object",
                        "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}},
                        "required": ["doctype", "name"]},
    },
    {
        "name": "count_documents",
        "description": "Count matching documents.",
        "inputSchema": {"type": "object",
                        "properties": {"doctype": {"type": "string"}, "filters": {"type": "object"}},
                        "required": ["doctype"]},
    },
    {
        "name": "create_document",
        "description": "Create one document. Values validated by Frappe.",
        "inputSchema": {"type": "object",
                        "properties": {"doctype": {"type": "string"}, "data": {"type": "object"}},
                        "required": ["doctype", "data"]},
    },
    {
        "name": "update_document",
        "description": "Update one document.",
        "inputSchema": {"type": "object",
                        "properties": {"doctype": {"type": "string"}, "name": {"type": "string"},
                                       "data": {"type": "object"}},
                        "required": ["doctype", "name", "data"]},
    },
    {
        "name": "delete_document",
        "description": "Delete one document. Requires delete permission.",
        "inputSchema": {"type": "object",
                        "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}},
                        "required": ["doctype", "name"]},
    },
    {
        "name": "call_method",
        "description": "Call a whitelisted server-side API method.",
        "inputSchema": {"type": "object",
                        "properties": {"method": {"type": "string"}, "args": {"type": "object"}},
                        "required": ["method"]},
    },
    {
        "name": "run_report",
        "description": "Run a Frappe report (query/script/report view) the user can access.",
        "inputSchema": {
            "type": "object",
            "properties": {"report": {"type": "string"}, "filters": {"type": "object"}},
            "required": ["report"],
        },
    },
]


def _rpc(result, id=None):
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _tool_call(name, args):
    if name == "search_doctypes":
        return frappe.get_all("DocType", filters={"name": ("like", f"%{args['query']}%"),
                                                  "istable": 0},
                              fields=["name", "module"], limit_page_length=30)
    if name == "get_doctype_schema":
        if not frappe.has_permission(args["doctype"], "read"):
            raise frappe.PermissionError
        meta = frappe.get_meta(args["doctype"])
        return [{"fieldname": f.fieldname, "label": f.label,
                 "fieldtype": f.fieldtype, "options": f.options,
                 "reqd": f.reqd} for f in meta.fields]
    if name == "list_documents":
        return frappe.get_all(args["doctype"],
                              filters=args.get("filters") or [],
                              fields=args.get("fields") or ["name"],
                              limit_page_length=min(int(args.get("limit") or 20), 200),
                              order_by=args.get("order_by") or "modified desc",
                              ignore_permissions=False)
    if name == "get_document":
        frappe.has_permission(args["doctype"], "read", throw=True)
        return frappe.get_doc(args["doctype"], args["name"])
    if name == "count_documents":
        return {"count": frappe.db.count(args["doctype"], args.get("filters") or [])}
    if name == "create_document":
        doc = frappe.get_doc({"doctype": args["doctype"], **(args["data"] or {})})
        doc.insert()
        return {"name": doc.name}
    if name == "update_document":
        doc = frappe.get_doc(args["doctype"], args["name"])
        doc.update(args["data"] or {})
        doc.save()
        return {"name": doc.name, "modified": str(doc.modified)}
    if name == "delete_document":
        frappe.delete_doc(args["doctype"], args["name"])
        return {"deleted": args["name"]}
    if name == "call_method":
        method = args["method"]
        if not frappe.get_attr(method).is_whitelisted:
            raise frappe.PermissionError
        return frappe.call(frappe.get_attr(method), **(args.get("args") or {}))
    if name == "run_report":
        from frappe.desk.query_report import run
        return run(report_name=args["report"], filters=args.get("filters") or {},
                   user=frappe.session.user)
    raise frappe.NotFound(_("Unknown tool: {0}").format(name))


MCP_PROTOCOL_VERSION = "2025-06-18"


@frappe.whitelist(methods=["POST"])
def handle():
    """MCP JSON-RPC entry point. Runs as the authenticated session user."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)

    try:
        req = json.loads(frappe.request.data or b"{}")
    except json.JSONDecodeError:
        return _rpc({"error": {"code": -32700, "message": "Parse error"}})

    method, params, id = req.get("method"), req.get("params") or {}, req.get("id")

    if method == "initialize":
        return _rpc({
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "frappe-mcp", "version": "0.2.0"},
        }, id)
    if method in ("notifications/initialized", None):
        return {}
    if method == "ping":
        return _rpc({}, id)
    if method == "tools/list":
        return _rpc({"tools": TOOLS}, id)
    if method == "tools/call":
        try:
            out = _tool_call(params["name"], params.get("arguments") or {})
            return _rpc({"content": [{"type": "text",
                                      "text": json.dumps(out, default=str, ensure_ascii=False)}]},
                        id)
        except Exception as e:
            frappe.log_error("frappe_mcp")
            return _rpc({"content": [{"type": "text", "text": str(e)}], "isError": True}, id)
    return _rpc({"error": {"code": -32601, "message": f"Method not found: {method}"}}, id)
