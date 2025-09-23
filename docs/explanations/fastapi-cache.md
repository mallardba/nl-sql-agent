# FastAPI & Cache System Explanation

## 🚀 **What FastAPI Does:**

FastAPI is a **web framework** that creates a **long-running Python process** (server) that:

1. **Starts up** → Loads your Python code (`app/` directory)
2. **Stays running** → Listens for HTTP requests on a port (8000)
3. **Handles requests** → Routes them to your functions
4. **Keeps state** → Maintains variables, objects, connections in memory

## 📁 **The `app/` Directory:**

The `app/` directory contains your **Python modules** that get **imported and loaded** when FastAPI starts:

```
app/
├── main.py      ← FastAPI app definition
├── agent.py     ← Your AI logic
├── cache.py     ← Cache system (_store object)
├── tools.py     ← Database tools
└── charts.py    ← HTML generation
```

## 🧠 **Why FastAPI Holds `_store`:**

When you start the server with `python run_server.py`:

1. **Python imports** all modules in `app/`
2. **`cache.py` executes** → `_store = {}` is created in memory
3. **FastAPI starts** → Server process begins
4. **Server stays alive** → `_store` remains in memory
5. **Requests come in** → Functions can access `_store`

## 🔄 **The Process Flow:**

```
1. python run_server.py
   ↓
2. FastAPI loads app/main.py
   ↓
3. main.py imports app/agent.py
   ↓
4. agent.py imports app/cache.py
   ↓
5. cache.py creates _store = {} in memory
   ↓
6. FastAPI starts listening on port 8000
   ↓
7. Server stays running with _store in memory
   ↓
8. HTTP requests → Functions use _store
```

## 🗄️ **How Your Cache Works:**

### **💾 Cache Storage:**
- **In-Memory Dictionary** - `_store: Dict[str, Tuple[Any, Optional[float]]]`
- **Key Format** - `"q::{question.lower().strip()}"` (e.g., `"q::what are the top 5 products?"`)
- **Value Format** - `(result_data, expiration_timestamp)`

### **⏰ Cache Lifecycle:**
1. **TTL (Time To Live)** - 15 minutes (`_TTL_SECONDS = 15 * 60`)
2. **Max Size** - 1000 entries (`_MAX_SIZE = 1000`)
3. **Auto-Cleanup** - Expired entries removed automatically

### **🔄 Cache Behavior:**

**When a question is asked:**
1. **Check cache first** - Look for `"q::{question}"`
2. **If found & not expired** - Return cached result immediately
3. **If not found or expired** - Generate new result, cache it, return it

**Cache Management:**
- **Automatic pruning** - Removes expired entries
- **Size limiting** - Removes oldest entries when cache is full (FIFO)
- **Process-local** - Cache exists only while the server is running

## 🚨 **Important Limitation:**

### **❌ Cache Does NOT Persist Between Server Restarts:**

```python
# This is an IN-MEMORY cache
_store: Dict[str, Tuple[Any, Optional[float]]] = {}
```

**What this means:**
- ✅ **Within same session** - Repeated questions are cached
- ❌ **Between server restarts** - Cache is completely lost
- ❌ **Between program runs** - No persistence to disk/database

## 🎯 **Cache Flow Example:**

```
1st run: "Top 5 products?" → AI generates SQL → Cache result → Return result
2nd run: "Top 5 products?" → Cache hit! → Return cached result (fast!)
Server restart: Cache cleared
3rd run: "Top 5 products?" → Cache miss → AI generates SQL again
```

## 🚀 **What FastAPI Actually Expects:**

FastAPI expects a **Python module** that contains an **app object** (FastAPI instance). The structure can be:

### **Option 1: Single File**
```
main.py  ← Contains: app = FastAPI()
```

### **Option 2: Package Structure (Your Current Setup)**
```
app/
├── __init__.py  ← Makes it a Python package
├── main.py      ← Contains: app = FastAPI()
├── agent.py     ← Other modules
└── cache.py     ← Other modules
```

### **Option 3: Different Structure**
```
src/
├── api/
│   ├── __init__.py
│   └── main.py  ← Contains: app = FastAPI()
└── models/
    └── database.py
```

## 🎯 **Your Current Setup:**

When you run:
```bash
python -m uvicorn app.main:app
```

This tells uvicorn:
- **`app.main`** - Import from the `app` package's `main.py` file
- **`:app`** - Use the `app` variable (FastAPI instance)

## 📁 **The `app/` Directory Choice:**

You chose `app/` as the package name, but you could have used:
- `api/`
- `server/`
- `backend/`
- `nl_sql_agent/`
- Or just put everything in `main.py`

## 💡 **Key Point:**

**FastAPI doesn't care about directory names** - it just needs:
1. **A Python package** (directory with `__init__.py`)
2. **A module** with an `app = FastAPI()` object
3. **The correct import path** when starting the server

Your `app/` directory is just a **good organizational choice** for structuring your code!

## 🚀 **For Production:**

If you need **persistent caching**, you'd replace this with:
- **Redis** - External cache server
- **Database** - Store cache in MySQL/SQLite
- **File cache** - Save to disk as JSON files

But for your current use case (development, demo, portfolio), the in-memory cache is perfect!

## 💡 **Analogy:**

Think of FastAPI like a **restaurant**:
- **Kitchen (app/)** - Your code and tools
- **Chef (FastAPI)** - Keeps the kitchen running
- **Ingredients (_store)** - Stored in the kitchen
- **Customers (HTTP requests)** - Come and go
- **Kitchen stays open** - Until you close the restaurant

The `_store` object lives in the "kitchen" (server memory) as long as the "restaurant" (FastAPI server) is open!
