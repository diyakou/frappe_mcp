"""MCP server for Frappe v15 — per-user login, task management."""
import os

import requests
from mcp.server.fastmcp import FastMCP

FRAPPE_URL = os.environ.get("FRAPPE_URL", "").rstrip("/")

mcp = FastMCP("frappe-tasks")
_state: dict = {"cookies": None, "user": None}


def _call(method: str, payload: dict | None = None, http: str = "POST") -> dict:
    if not _state["cookies"]:
        raise RuntimeError("Not logged in. Call frappe_login first.")
    url = f"{FRAPPE_URL}/api/method/{method}"
    r = requests.request(http, url, json=payload if http == "POST" else None,
                         params=payload if http == "GET" else None,
                         cookies=_state["cookies"], timeout=30)
    r.raise_for_status()
    return r.json().get("message", r.json())


@mcp.tool()
def frappe_login(usr: str, pwd: str) -> str:
    """Log in to Frappe with your own username and password."""
    s = requests.Session()
    r = s.post(f"{FRAPPE_URL}/api/method/login", data={"usr": usr, "pwd": pwd}, timeout=30)
    r.raise_for_status()
    _state["cookies"] = s.cookies.get_dict()
    _state["user"] = r.json().get("message")  # full_name or 'Logged In'
    return f"Logged in as {usr}"


@mcp.tool()
def my_tasks(status: str = "", limit: int = 20) -> list:
    """List my tasks (ToDo). Frappe applies user permissions. Optional status filter."""
    filters = {}
    if status:
        filters["status"] = status
    return _call("frappe.client.get_list", {
        "doctype": "ToDo", "filters": filters,
        "fields": ["name", "description", "status", "date", "priority"],
        "limit_page_length": limit, "order_by": "date desc",
    }, http="GET")


@mcp.tool()
def get_task(name: str) -> dict:
    """Get one task (ToDo) by name. Returns only fields you're permitted to read."""
    return _call("frappe.client.get", {"doctype": "ToDo", "name": name}, http="GET")


@mcp.tool()
def create_task(description: str, date: str = "", priority: str = "Low",
                allocated_to: str = "") -> dict:
    """Create a ToDo. allocated_to defaults to the logged-in user."""
    data = {"description": description, "priority": priority}
    if date:
        data["date"] = date
    if allocated_to:
        data["allocated_to"] = allocated_to
    return _call("frappe.client.insert", {"doc": {"doctype": "ToDo", **data}})


@mcp.tool()
def update_task(name: str, status: str = "", priority: str = "", date: str = "") -> dict:
    """Update task status (Open/Closed/Cancelled), priority or date."""
    data = {k: v for k, v in {"status": status, "priority": priority, "date": date}.items() if v}
    return _call("frappe.client.set_value",
                 {"doctype": "ToDo", "name": name, "fieldname": data})


@mcp.tool()
def complete_task(name: str) -> str:
    """Mark a task as Closed."""
    _call("frappe.client.set_value", {"doctype": "ToDo", "name": name,
                                      "fieldname": {"status": "Closed"}})
    return f"{name} closed"


@mcp.tool()
def add_comment(name: str, text: str) -> str:
    """Add a comment to a task."""
    _call("frappe.desk.form.comment.add_comment",
          {"doc": {"doctype": "ToDo", "name": name}, "text": text,
           "comment_email": _state["user"]})
    return "Comment added"


@mcp.tool()
def my_profile() -> dict:
    """Show who is logged in."""
    return _call("frappe.auth.get_logged_user", http="GET")


if __name__ == "__main__":
    mcp.run()
