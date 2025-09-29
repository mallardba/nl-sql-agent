# Import Contexts: Uvicorn vs Pytest

## The Problem

When developing Python applications, you might encounter import errors that work in one context (like running the application) but fail in another (like running tests). This document explains why this happens and how to solve it.

## The Issue We Encountered

Our `app/config/metrics_config.py` file needed to import from `app/enums.py`. We tried different import approaches:

1. **Relative import**: `from ..enums import SQLSource`
2. **Absolute import**: `from app.enums import SQLSource`
3. **Direct import**: `from enums import SQLSource`

Each approach worked in some contexts but failed in others.

## Why Different Import Contexts Matter

### Uvicorn Context

When you run your FastAPI application with uvicorn:

```bash
uvicorn app.main:app --reload
```

**How imports work:**
- Uvicorn treats `app` as a Python package (app.main:app is the package path)
- The current working directory is the project root (`nl-sql-agent/`) where you run the uvicorn command
- Python can resolve relative imports within the package structure
- `from ..enums import SQLSource` works because it goes up one level from `app/config/` to `app/` and finds `enums.py`

**Import resolution:**
```
Project Root/
├── app/
│   ├── __init__.py
│   ├── enums.py          ← Target file
│   └── config/
│       ├── __init__.py
│       └── metrics_config.py  ← Source file (uses ..enums)
```

### Pytest Context

When you run pytest:

```bash
pytest
```

**How imports work:**
- Pytest treats the directory containing `pytest.ini` as the test root
- By default, pytest doesn't automatically add your project directories to the Python path
- Relative imports can fail because pytest might not recognize the package structure
- `from ..enums import SQLSource` fails with "attempted relative import beyond top-level package"

## The Solution

We used a **try/except fallback pattern**:

```python
try:
    from ..enums import SQLSource  # Works for uvicorn
except ImportError:
    from enums import SQLSource    # Works for pytest
```

Combined with pytest configuration:

```ini
# pytest.ini
[pytest]
addopts = -q
asyncio_mode = auto
pythonpath = .
```

## How This Solution Works

### For Uvicorn
1. **First attempt**: `from ..enums import SQLSource` succeeds
2. **No fallback needed**: The relative import works because uvicorn recognizes the package structure

### For Pytest
1. **First attempt**: `from ..enums import SQLSource` fails with ImportError
2. **Fallback**: `from enums import SQLSource` succeeds because `pythonpath = .` tells pytest to treat the current directory (`nl-sql-agent/`) as the root, and it can find `enums.py` in the `app/` subdirectory
3. **Result**: Pytest can find `enums.py` at `app/enums.py` relative to the project root

**Note**: The fallback import `from enums import SQLSource` works because:
- `pythonpath = .` adds `nl-sql-agent/` to the Python path (sys.path)
- Python looks for `enums.py` in all directories on the path
- It finds `app/enums.py` and imports it as `enums`

**Why `from app.enums import SQLSource` won't work in the fallback:**
- This would require `app` to be a proper Python package with `__init__.py`
- The fallback is designed to work even if the package structure isn't fully recognized
- `from enums import SQLSource` is a direct file import that bypasses package structure

**Important Note**: We use `pythonpath = .` (not `pythonpath = app`) because:
- Tests in the `tests/` directory need to import from `app` (e.g., `from app.main import app`)
- If we set `pythonpath = app`, pytest can't find the `app` module because it becomes the root
- With `pythonpath = .`, both the `app` package and `tests` directory are accessible
- `pythonpath` in pytest.ini is equivalent to adding directories to `sys.path`

## Alternative Solutions

### Option 1: Always Use Absolute Imports
```python
from app.enums import SQLSource
```
- **Pros**: Explicit, clear, works everywhere
- **Cons**: Requires `app` to be in Python path, longer import paths

### Option 2: Configure Python Path
Add to your environment or startup script:
```bash
export PYTHONPATH="${PYTHONPATH}:."
```
- **Pros**: Makes absolute imports work consistently
- **Cons**: Environment-dependent, not portable

### Option 3: Use sys.path Manipulation
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enums import SQLSource
```
- **Pros**: Works in all contexts
- **Cons**: More complex, harder to maintain

## Best Practices

1. **Use relative imports within packages**: `from ..module import something`
2. **Configure pytest properly**: Use `pythonpath` in `pytest.ini`
3. **Test your imports**: Verify both uvicorn and pytest work
4. **Document import strategies**: Explain why certain patterns are used
5. **Consider package structure**: Design your package hierarchy to minimize import complexity

## Key Takeaways

- **Different tools have different import contexts**
- **Uvicorn recognizes package structure, pytest might not**
- **Use try/except patterns for cross-context compatibility**
- **Configure pytest with `pythonpath` for consistent behavior**
- **Test your imports in all execution contexts**

## Related Concepts

- **Python Package Structure**: How `__init__.py` files define packages
- **PYTHONPATH Environment Variable**: How Python finds modules
- **Relative vs Absolute Imports**: When to use each approach
- **Pytest Configuration**: How to configure test discovery and execution
