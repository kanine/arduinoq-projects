# arduino-dbstorage-sqlstore

Skill for working with the Arduino Uno Q `dbstorage_sqlstore` brick and the `SQLStore` Python API.

## Overview

This brick helps manage SQLite databases through a simple interface for creating tables, inserting data, and handling database connections.

The Database - SQL brick allows you to:

- use a simple API for SQLite database operations
- create tables with custom schemas
- insert, update, and delete records
- query data with flexible filters
- manage connections automatically
- handle errors for common database issues

It provides thread-safe database operations using SQLite as the underlying database engine. It supports named access to columns for easier data handling. The brick also manages database file storage in a dedicated directory structure and handles the connection lifecycle.

## Features

- thread-safe database operations for multi-threaded applications
- automatic table creation with type inference from data
- flexible querying with `WHERE`, `ORDER BY`, and `LIMIT`
- schema management with column addition and removal capabilities
- raw SQL execution for advanced cases
- named column access using `sqlite3.Row`

## Files

- `SKILL.md`: trigger metadata and operating guidance for Codex
- `references/sqlstore-api.md`: API reference formatted from the provided documentation
- `agents/openai.yaml`: UI metadata for the skill

## Code Example And Usage

Instantiate a new class to open or create a database:

```python
from arduino.app_bricks.dbstorage_sqlstore import SQLStore

db = SQLStore("example.db")
# ... do work

# Close database
db.stop()
```

Create a table:

```python
columns = {
    "id": "INTEGER PRIMARY KEY",
    "name": "TEXT",
    "age": "INTEGER"
}
db.create_table("users", columns)
```

Insert data into a table:

```python
data = {
    "name": "Alice",
    "age": 30
}
db.store("users", data)
```

Official App Lab example:

```python
# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

# EXAMPLE_NAME = "Store and read data using SQLStore"
from arduino.app_bricks.dbstorage_sqlstore import SQLStore

db = SQLStore("example.db")

# Create a table
columns = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "age": "INTEGER"}
db.create_table("users", columns)

# Insert data
data = {"name": "Alice", "age": 30}
db.store("users", data)

# Read data
result = db.read("users")
print(result)

# Drop the table
db.drop_table("users")
```

## Understanding Database Operations

The `SQLStore` automatically creates a directory structure for database storage and places database files under `data/dbstorage_sqlstore/` within the application directory.

The brick supports automatic type inference when creating tables from inserted data:

- `int` -> `INTEGER`
- `float` -> `REAL`
- `str` -> `TEXT`
- `bytes` -> `BLOB`

The `store()` method can create tables automatically by inspecting the provided values. This is useful for quick starts and append-only logs. For stable application data, explicit schemas are still the safer default because they give you control over column definitions and constraints.

## Current Scope

- SQLStore lifecycle
- table creation and replacement
- CRUD operations
- raw SQL execution
- schema migration behavior

## Next Inputs That Would Improve The Skill

- your preferred overview text
- Uno Q-specific usage examples
- any house conventions for table naming, retention, or migration policy
