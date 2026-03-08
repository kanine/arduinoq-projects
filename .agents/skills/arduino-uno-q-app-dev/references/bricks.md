# Arduino App Bricks

Bricks are modular components that provide specialized functionality to an app. They are declared in `app.yaml` under the `bricks:` section.

## Common Bricks

### `arduino:web_ui`

Provides a high-level Python API for creating web dashboards and exposing REST/Socket.io interfaces.

**app.yaml declaration:**
```yaml
bricks:
- arduino:web_ui: {}
```

**Python usage:**
```python
from arduino.app_bricks.web_ui import WebUI
ui = WebUI()

# Expose an API
def my_handler(payload):
    return {"status": "ok"}
ui.expose_api('POST', '/my_endpoint', my_handler)

# Assets
# By default, looks for index.html in the assets/ folder.
```

### `arduino:dbstorage_sqlstore`

Provides a persistent SQLite database for the app.

**app.yaml declaration:**
```yaml
bricks:
- arduino:dbstorage_sqlstore: {}
```

**Python usage:**
```python
from arduino.app_bricks.dbstorage_sqlstore import SQLStore
db = SQLStore()

# The SQLStore typically handles connection and basic table management.
# See copy-of-led-matrix-painter/python/store.py for real-world usage.
```

## Configuring Bricks

Each brick can have its own configuration in `app.yaml`. If no special configuration is needed, use an empty object `{}`.

Example of multiple bricks:
```yaml
bricks:
- arduino:web_ui: {}
- arduino:dbstorage_sqlstore: {}
```
