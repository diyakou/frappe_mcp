from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="frappe_mcp",
    version="0.2.0",
    description="MCP server endpoint for Frappe v15 — per-user permission access",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ClickERP",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.8",
)
