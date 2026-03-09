---
name: arduino-dbstorage-sqlstore
description: Use when working with the Arduino Uno Q `dbstorage_sqlstore` brick or the `SQLStore` Python API for persisted application data. Apply this skill for Uno Q app tasks involving schema design, creating tables, storing records, reading filtered rows, updating or deleting records, running raw SQL, or migrating table schemas with `create_or_replace_table`. Trigger when a task mentions `dbstorage_sqlstore`, `SQLStore`, SQLite-backed app storage, or persistent logs/configuration in Uno Q Python apps.
---

# DBStorage SQLStore

Use this skill for Uno Q Python applications that persist data with the `dbstorage_sqlstore` brick. Keep the workflow here short and load [references/sqlstore-api.md](references/sqlstore-api.md) when exact method signatures, defaults, or schema-migration behavior matters.

## Quick Start

1. Confirm the app uses the `arduino:dbstorage_sqlstore` brick in `app.yaml`.
2. Keep persistence on the MPU Python side.
3. Instantiate one `SQLStore` for the app database file.
4. Prefer explicit table schemas for stable app data.
5. Use raw `execute_sql()` only when the higher-level methods are insufficient.

## Default Pattern

Use this baseline structure in `python/main.py`:

```python
from arduino.app_bricks.dbstorage_sqlstore import SQLStore

store = SQLStore("app-data.db")
store.create_table("events", {
    "id": "INTEGER PRIMARY KEY",
    "timestamp": "TEXT",
    "event_type": "TEXT",
    "payload": "TEXT",
})
store.store("events", {
    "timestamp": "2026-03-09T12:00:00Z",
    "event_type": "started",
    "payload": "{}",
})
rows = store.read("events", order_by="timestamp DESC", limit=20)
```

## Design Rules

- Prefer `create_table()` or `create_or_replace_table()` over implicit schema inference when the data model matters.
- Use `store()` with automatic table creation only for simple append-only data or quick prototypes.
- Keep table names and column names stable because UI and API code often couple to them.
- Treat `condition` and `order_by` arguments as SQL fragments; construct them carefully and avoid passing unchecked user text.
- Keep schema migrations deliberate. Use `create_or_replace_table()` when you need controlled evolution.
- Catch `DBStorageSQLStoreError` around startup, migrations, and user-triggered writes.

## Recommended Task Flows

### Logs And Event Tables

1. Define a narrow append-only schema.
2. Create the table at startup.
3. Insert with `store()`.
4. Read recent rows with `order_by` and `limit`.
5. Expose filtered results through `web_ui` APIs.

### Configuration Storage

1. Use a dedicated config table.
2. Read config on startup.
3. Validate values in Python before writing.
4. Update specific rows with `update()`.

### Schema Migration

1. Prefer additive changes when possible.
2. Use `create_or_replace_table()` to reconcile the live schema with the expected schema.
3. Only enable `force_drop_table=True` when losing existing table data is acceptable.

## Uno Q Guidance

- Use this skill together with Uno Q app skills when the app exposes stored data through `web_ui`.
- Keep high-frequency hardware traffic out of the database path; persist summarized events or completed cycles instead.
- For operator dashboards, use `read(..., order_by=..., limit=...)` to serve recent data efficiently.

## Reference File

Load [references/sqlstore-api.md](references/sqlstore-api.md) for:

- class and method signatures
- parameter defaults
- exception behavior
- schema migration semantics
- suggested usage patterns derived from the API
