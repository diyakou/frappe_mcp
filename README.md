# Frappe MCP

اپ MCP برای Frappe v15 — endpoint Streamable HTTP روی خود سرور، هر یوزر با
token خودش وصل می‌شه و فقط به دیتای مجاز خودش دسترسی داره.

**سایت:** `https://simple.clickapps.ir`

## نصب روی سرور

```bash
cd /home/clickerp/frappe-bench
bench get-app frappe_mcp https://github.com/diyakou/frappe_mcp
bench --site simple.clickapps.ir install-app frappe_mcp
bench --site simple.clickapps.ir migrate
bench restart
```

## Endpoint

```
POST https://simple.clickapps.ir/api/method/frappe_mcp.mcp.handle
```

Streamable HTTP MCP — متدهای `initialize`, `tools/list`, `tools/call`, `ping`, `DELETE`.
Auth: header `Authorization: token API_KEY:API_SECRET` (User → API Access → Generate Keys).

## اتصال کلاینت (بدون adapter)

opencode:
```json
{
  "mcp": {
    "frappe": {
      "type": "remote",
      "url": "https://simple.clickapps.ir/api/method/frappe_mcp.mcp.handle",
      "headers": { "Authorization": "token KEY:SECRET" }
    }
  }
}
```

Claude Code:
```bash
claude mcp add --transport http frappe https://simple.clickapps.ir/api/method/frappe_mcp.mcp.handle \
  --header "Authorization: token KEY:SECRET"
```

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
curl -X POST https://simple.clickapps.ir/api/method/frappe_mcp.mcp.handle \
  -H "Content-Type: application/json" \
  -H "Authorization: token KEY:SECRET" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

بدون auth باید 401 بده — یعنی endpoint فعاله.

## امنیت

- Permission چک سمت Frappe انجام می‌شه؛ هر یوزر فقط دیتای role خودش.
- `MCP Call Log` برای دیدن اینکه کی چه call ای زده.
- Secret رو تو git یا جای عمومی نذار.
