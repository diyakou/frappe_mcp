"""Self-check: TOOLS well-formed (parses without frappe installed)."""
import ast

src = open("frappe_mcp/mcp.py", encoding="utf-8").read()
tree = ast.parse(src)

# extract TOOLS literal
tools = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TOOLS" for t in node.targets):
        tools = ast.literal_eval(node.value)
assert tools, "TOOLS not found"
names = [t["name"] for t in tools]
assert len(names) == len(set(names)), "duplicate tool names"
assert all("inputSchema" in t and "description" in t for t in tools), "bad tool def"
print(f"OK — {len(names)} tools: {names}")
