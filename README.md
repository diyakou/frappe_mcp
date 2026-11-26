# Frappe MCP

اپ MCP برای Frappe v15 — endpoint روی خود سرور نصب می‌شه، هر یوزر با
session خودش وصل می‌شه و فقط به دیتای مجاز خودش دسترسی داره.

**سایت:** `https://erp.clickapps.ir`

## نصب روی سرور

```bash
cd /home/clickerp/frappe-bench
bench get-app frappe_mcp https://github.com/diyakou/frappe_mcp
bench --site erp.clickapps.ir install-app frappe_mcp
bench --site erp.clickapps.ir migrate
bench restart
```

## Endpoint

```
POST https://erp.clickapps.ir/api/method/frappe_mcp.mcp.handle
```

JSON-RPC 2.0 — متدهای `initialize`, `tools/list`, `tools/call`, `ping`.
Auth: session کوکی یا token عادی Frappe. Guest → `PermissionError`.

## Tools

| Tool | کار |
|---|---|
| `search_doctypes` | پیدا کردن DocType ها |
| `get_doctype_schema` | فیلدهای یک DocType |
| `list_documents` | لیست داکیومنت‌ها با filter |
| `get_document` | خوندن یک داکیومنت |
| `count_documents` | شمارش |
| `create_document` | ایجاد |
| `update_document` | ویرایش |
| `delete_document` | حذف |
| `call_method` | صدا زدن متد whitelisted |
| `run_report` | اجرای گزارش |

## لاگ (Audit)

هر `tools/call` در DocType **MCP Call Log** ثبت می‌شه: user, tool, arguments,
success, error, duration. فقط System Manager می‌بینه.
Desk → search "MCP Call Log".

## تست

```bash
curl -X POST https://erp.clickapps.ir/api/method/frappe_mcp.mcp.handle \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

بدون login باید `PermissionError` بده — یعنی endpoint فعاله.

## امنیت

- Permission چک سمت Frappe انجام می‌شه؛ هر یوزر فقط دیتای role خودش.
- `MCP Call Log` برای دیدن اینکه کی چه call ای زده.
