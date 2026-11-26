# Frappe Tasks MCP

MCP server برای Frappe v15 — هر یوزر با username/password خودش login می‌کنه،
تسک‌هاش (ToDo) رو مدیریت می‌کنه. Permission ها رو خود Frappe اعمال می‌کنه.

## اجرا

```bash
pip install -r requirements.txt
FRAPPE_URL=https://your-site.com python server.py
```

## Tools

| Tool | کار |
|---|---|
| `frappe_login(usr, pwd)` | ورود هر یوزر با پسورد خودش |
| `my_tasks(status, limit)` | لیست تسک‌های من |
| `get_task(name)` | دیدن یک تسک |
| `create_task(description, date, priority, allocated_to)` | ایجاد تسک |
| `update_task(name, status, priority, date)` | ویرایش تسک |
| `complete_task(name)` | بستن تسک |
| `add_comment(name, text)` | کامنت گذاشتن |
| `my_profile()` | کاربر لاگین‌شده |

## اتصال به Claude Desktop

```json
{
  "mcpServers": {
    "frappe-tasks": {
      "command": "python",
      "args": ["E:/project/frappe_mcp/server.py"],
      "env": { "FRAPPE_URL": "https://your-site.com" }
    }
  }
}
```

## امنیت

- Login روی همه session ها مشترکه (یک کاربر در لحظه). چند کاربر همزمان =
  چند instance جدا از سرور، یا اضافه کردن session-per-connection.
- پسوردها ذخیره نمی‌شن — فقط کوکی session در حافظه.
- `/api/method/login` با auth لاگین Frappe کار می‌کنه؛ permission چک سرور Frappe انجام میشه.
