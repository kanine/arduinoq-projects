# SQLStore API Reference

This reference is formatted from the API documentation provided by the user.

The user also provided an App Lab example named `Store and read data using SQLStore`. That example covers the minimal flow: instantiate `SQLStore`, create a table, store a row, read rows, and drop the table.

## Index

- `DBStorageSQLStoreError`
- `SQLStore`
- `SQLStore.start()`
- `SQLStore.stop()`
- `SQLStore.create_table()`
- `SQLStore.drop_table()`
- `SQLStore.store()`
- `SQLStore.read()`
- `SQLStore.update()`
- `SQLStore.delete()`
- `SQLStore.execute_sql()`
- `SQLStore.create_or_replace_table()`

## DBStorageSQLStoreError

```python
class DBStorageSQLStoreError()
```

Exception raised for SQLite database operation errors.

Raised for failures such as:

- connection errors
- SQL syntax errors
- constraint violations
- table access issues

## SQLStore

```python
class SQLStore(database_name: str)
```

SQLite storage client for storing and retrieving data.

Key properties from the provided API text:

- uses SQLite as the storage engine
- supports named column access using `sqlite3.Row`
- designed to be thread-safe
- suitable for multi-threaded applications
- stores database files under `data/dbstorage_sqlstore/` within the application directory

### Constructor

Parameters:

- `database_name: str = "arduino.db"`: SQLite database filename

## start

```python
start()
```

Open the SQLite database connection.

Notes:

- establishes the database connection
- should be called before database operations
- enables named column access through the row factory

Raises:

- `DBStorageSQLStoreError`

## stop

```python
stop()
```

Close the SQLite database connection.

Raises:

- `DBStorageSQLStoreError`

## create_table

```python
create_table(table: str, columns: dict[str, str])
```

Create a table if it does not already exist.

Parameters:

- `table`: table name
- `columns`: mapping of column names to SQL types

Common column types from the provided docs:

- `"INTEGER"`
- `"REAL"`
- `"TEXT"`
- `"BLOB"`
- `"INTEGER PRIMARY KEY"`

Raises:

- `DBStorageSQLStoreError`

## drop_table

```python
drop_table(table: str)
```

Remove a table and all its data permanently.

Parameters:

- `table`: table name

Raises:

- `DBStorageSQLStoreError`

## store

```python
store(table: str, data: dict[str, Any], create_table: bool = True)
```

Insert data into a table. By default, create the table if it does not exist.

Parameters:

- `table`: destination table name
- `data`: column/value mapping
- `create_table`: if `True`, create the table automatically using inferred types

Supported value types from the provided docs:

- `int` -> `INTEGER`
- `float` -> `REAL`
- `str` -> `TEXT`
- `bytes` -> `BLOB`

Behavior note from the provided overview:

- automatic table creation uses type inference based on the provided values

Raises:

- `DBStorageSQLStoreError`

## read

```python
read(
    table: str,
    columns: Optional[list] = None,
    condition: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = -1,
)
```

Read rows from a table with optional filtering.

Parameters:

- `table`: source table
- `columns`: selected columns, or `None` for all columns
- `condition`: SQL `WHERE` fragment such as `"age > 18"`
- `order_by`: SQL `ORDER BY` fragment such as `"name ASC"`
- `limit`: max rows to return, `-1` for no limit

Returns:

- `list[dict[str, Any]]`
- returns an empty list if the table does not exist

Raises:

- `DBStorageSQLStoreError`

## update

```python
update(table: str, data: dict[str, Any], condition: Optional[str] = "")
```

Update existing records.

Parameters:

- `table`: target table
- `data`: columns and replacement values
- `condition`: SQL `WHERE` fragment; if empty, updates all rows

Raises:

- `DBStorageSQLStoreError`

## delete

```python
delete(table: str, condition: Optional[str] = "")
```

Delete records from a table.

Parameters:

- `table`: target table
- `condition`: SQL `WHERE` fragment; if empty, deletes all rows

Raises:

- `DBStorageSQLStoreError`

## execute_sql

```python
execute_sql(sql: str, args: Optional[tuple] = None)
```

Execute raw SQL.

Parameters:

- `sql`: SQL command text
- `args`: optional positional parameters

Returns:

- `list[dict[str, Any]] | None`
- returns rows as dictionaries if the command yields rows
- returns `None` when the command does not yield rows

Raises:

- `DBStorageSQLStoreError`

## create_or_replace_table

```python
create_or_replace_table(
    table: str,
    columns: dict[str, str],
    force_drop_table: bool,
)
```

Create or update a table to match the provided schema.

Important behavior from the provided docs:

- all schema changes happen in one transaction
- if an error occurs, the transaction is rolled back and the table remains unchanged
- if `force_drop_table` is `True`, the table is dropped and recreated after rollback
- if the table exists, missing columns are added
- extra columns are removed unless they are not-simple columns
- non-simple columns include things like:
  - primary key columns
  - unique columns
  - indexed columns
  - columns used by constraints, triggers, or views
- if a column type changes or a column is not simple, an error is raised unless `force_drop_table=True`
- forcing drop and recreate loses all existing data in that table

Parameters:

- `table`: target table
- `columns`: expected schema mapping
- `force_drop_table`: whether to allow destructive recovery

Raises:

- `DBStorageSQLStoreError`

## Suggested Usage Patterns

### Explicit schema for stable app data

```python
store.create_table("cycle_log", {
    "id": "INTEGER PRIMARY KEY",
    "timestamp": "TEXT",
    "speed_mm_per_s": "REAL",
    "status": "TEXT",
})
```

### Read recent rows

```python
rows = store.read(
    "cycle_log",
    order_by="timestamp DESC",
    limit=100,
)
```

### Update a single row

```python
store.update(
    "settings",
    {"relay_pulse_ms": 100},
    condition="profile = 'default'",
)
```

### Raw SQL when needed

```python
rows = store.execute_sql(
    "SELECT status, COUNT(*) AS count FROM cycle_log GROUP BY status"
)
```
