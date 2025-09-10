# Natural-Language SQL Analyst (Agentic AI)

Turn plain English questions into SQL for **MySQL**, execute them, and return **tables + charts**.
This starter includes a minimal **FastAPI** service, AI-powered SQL generation with **OpenAI**, 
embeddings for intelligent context, and test scaffolding you can extend.

## Quick start

### Note on MySQL
Section 2 (Run MySQL via Docker) is **optional**. You can use Docker Compose to spin up a MySQL 8 instance for convenience, or instead point `DATABASE_URL` to any existing MySQL 8 server (local install, WSL2, VM, or cloud service) where you have loaded `db/init.sql`.

### 1) Setup
- Copy `.env.example` → `.env` and fill in required values (e.g. your LLM API key, which you'll need once you integrate an LLM).
- If you're configuring the database, check `.env.template` for ready-made `DATABASE_URL` connection strings. Just copy the appropriate line for your environment (Docker, local install, AWS RDS, etc.) into your `.env`.
- Install Python 3.13

```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DB creds and LLM key (if using one)
```

#### Optional dev tools setup
```bash
pip install -r requirements-dev.txt
pre-commit install
```

This installs optional dev tools and sets up Git hooks.  
After this, black/isort/ruff/pytest will run automatically before every commit.

### 2) Run MySQL (optional, via Docker)
```bash
docker compose up -d db
# (re)load comprehensive schema + seed data
mysql -h 127.0.0.1 -P 3306 -u root -proot sales < db/init.sql
```

#### Example `DATABASE_URL` values
| Environment                  | Example Connection String                                                                 |
|------------------------------|-------------------------------------------------------------------------------------------|
| **Docker (from this repo)**  | `mysql+pymysql://root:root@localhost:3306/sales`                                          |
| **Local MySQL install**      | `mysql+pymysql://myuser:mypassword@127.0.0.1:3306/sales`                                  |
| **AWS RDS MySQL**            | `mysql+pymysql://admin:secret@mydb.abcdefghij.us-west-2.rds.amazonaws.com:3306/sales`     |
| **Azure Database for MySQL** | `mysql+pymysql://user@myserver:password@myserver.mysql.database.azure.com:3306/sales`     |
| **GCP Cloud SQL (public IP)**| `mysql+pymysql://user:password@<CLOUDSQL_IP>:3306/sales`                                  |

### 2.1) Verify connection
Run the test suite to confirm your database is reachable and seeded:

```bash
pytest tests/test_schema_loaded.py
```

### 3) OpenAI Setup (Required for AI features)
Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys) and configure it:

```bash
# Run the setup script
python setup_openai.py

# Or manually edit .env file
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

### 4) Embeddings Setup (Optional but recommended)
Set up ChromaDB for intelligent context and pattern learning:

```bash
# Set up Docker environment (includes embeddings storage)
python setup_docker_embeddings.py

# Or manually start containers
docker compose up -d

# Initialize schema embeddings
curl -X POST http://localhost:8000/embeddings/initialize

# Test embeddings setup
python test_embeddings.py
```

**Note:** Schema embeddings are **one-time setup** - you only need to run the initialization once. After that, the agent will automatically use the stored embeddings for all future questions. If you skip this step, the agent will still work but won't have the enhanced context from embeddings.

### 5) Run all tests (optional)
```bash
# Run all unit tests
pytest

# Test embeddings system (requires running server)
python test_embeddings.py
```

### 6) Launch API
```bash
# Production server
python run_server.py

# Debug server (with verbose output)
python run_debug_server.py

# Or manually
python -m uvicorn app.main:app --reload --port 8000
```

### 7) Try it
```bash
# JSON response
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Top 5 products by revenue last quarter?"}'

# HTML response with charts
curl -X POST "http://localhost:8000/ask?html=true" -H "Content-Type: application/json" -d '{"question":"Top 5 products by revenue last quarter?"}'

# Or use the convenience script
./ask-and-open.sh "Top 5 products by revenue last quarter?"
```


## Response Formats

### JSON Response (Default)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"sales by month"}'
```
Returns structured JSON with SQL, results, and optional chart data.

### HTML Response (With Charts)
```bash
curl -X POST "http://localhost:8000/ask?html=true" \
  -H "Content-Type: application/json" \
  -d '{"question":"sales by month"}'
```
Returns beautiful HTML page with embedded interactive charts and formatted tables.

### Browser Testing
```bash
# Visit in browser
http://localhost:8000/ask-html?question=sales%20by%20month
```

### Convenience Script
```bash
# One command to ask and open in browser
./ask-and-open.sh "sales by month"
```

## Features

### AI-Powered SQL Generation
- **OpenAI Integration** - Uses GPT models for intelligent SQL generation
- **Schema Awareness** - Understands your database structure
- **Fallback System** - Falls back to heuristic rules if AI fails
- **Configurable Models** - Support for different OpenAI models

### Embeddings & Intelligence
- **ChromaDB Integration** - Vector database for intelligent context
- **Schema Embeddings** - Database structure stored as embeddings
- **Pattern Learning** - Learns from successful queries
- **Similarity Search** - Finds relevant schema and questions

### Visualization
- **Interactive Charts** - Plotly-powered charts embedded in HTML
- **Responsive Design** - Works on desktop and mobile
- **Multiple Chart Types** - Bar, line, and more chart types
- **Formatted Tables** - Clean, readable data tables

### Performance & Reliability
- **Query Caching** - Caches results with TTL for faster responses
- **Error Handling** - Graceful fallbacks and error recovery
- **Docker Support** - Consistent environment with Docker
- **Health Checks** - System monitoring and status endpoints

## Reference


### Data model overview
- Rich schema: `customers`, `employees`, `regions`, `channels`, `categories`, `products`, `product_tags`, `inventories`, `promotions`, `orders`, `order_items`, `payments`, `shipments`, `returns`.
- Views: `v_product_revenue`, `v_monthly_sales`, `v_customer_ltv`.
- Helper: `fiscal_quarter(date)` (FY starts in April).
- Seed data spans 2024–2025 with cancellations, discounts, returns, multi-payments.

### Endpoints
- `POST /ask` → `{ question }` -> `{ answer_text, sql, rows, chart_json? }`
- `POST /ask?html=true` → `{ question }` -> HTML response with charts and tables
- `GET  /ask-html?question=...` → HTML response for browser testing
- `GET  /schema` → schema metadata
- `GET  /healthz` → health check
- `GET  /embeddings/status` → embeddings system status
- `POST /embeddings/initialize` → initialize schema embeddings


#### POST /ask
Turn a natural language question into SQL, execute it, and return results.

**Request**
```json
{
  "question": "Top 5 products by revenue last quarter?"
}
```

**Response**
```json
{
  "answer_text": "Here are the top 5 products by revenue for Q2 FY2025.",
  "sql": "SELECT p.product_name, SUM(oi.quantity*oi.unit_price) AS revenue ...",
  "rows": [
    {"product_name": "Widget A", "revenue": 12345.67},
    {"product_name": "Widget B", "revenue": 9876.54},
    {"product_name": "Widget C", "revenue": 8765.43},
    {"product_name": "Widget D", "revenue": 7654.32},
    {"product_name": "Widget E", "revenue": 6543.21}
  ],
  "chart_json": { "...": "plotly chart spec (optional)" }
}
```

#### POST /ask?html=true
Same as `/ask` but returns HTML with embedded charts and tables.

#### GET /ask-html?question=...
Simple GET endpoint for testing HTML responses in browser.

#### GET /schema
Retrieve schema metadata (tables, columns, views).

**Response**
```json
{
  "tables": {
    "customers": ["customer_id", "name", "region", "signup_date"],
    "orders": ["order_id", "customer_id", "order_date", "status"],
    "products": ["product_id", "name", "category", "price"]
  },
  "views": ["v_product_revenue", "v_monthly_sales", "v_customer_ltv"]
}
```

#### GET /embeddings/status
Check status of embeddings system.

**Response**
```json
{
  "status": "ok",
  "embeddings": {
    "schema_embeddings": 5,
    "question_embeddings": 0,
    "collections": ["schema_embeddings", "question_embeddings"]
  }
}
```

#### POST /embeddings/initialize
Initialize schema embeddings from database schema.

**Response**
```json
{
  "status": "success",
  "message": "Schema embeddings initialized successfully"
}
```

#### GET /healthz
Health check endpoint.

**Response**
```json
{ "ok": true }
```


### Project layout
```
nl-sql-agent/
├─ app/
│  ├─ main.py          # FastAPI app + routes
│  ├─ agent.py         # AI-powered SQL generation with OpenAI
│  ├─ tools.py         # SQL execution, schema lookup, chart tool
│  ├─ charts.py        # HTML chart builders and visualization
│  ├─ schema_index.py  # ChromaDB embeddings and vector search
│  ├─ cache.py         # Query caching with TTL
│  └─ models.py        # Pydantic models
├─ db/
│  └─ init.sql         # Example schema + seed data
├─ tests/
│  ├─ test_ask_endpoint.py
│  ├─ test_healthz.py
│  ├─ test_schema_loaded.py
│  ├─ test_sql_generation.py
│  └─ test_end_to_end.py
├─ scripts/
│  └─ monthly-sales-html.sh  # Example curl script
├─ requirements.txt
├─ requirements-dev.txt
├─ docker-compose.yml
├─ setup_openai.py     # OpenAI configuration script
├─ setup_docker_embeddings.py  # Docker embeddings setup
├─ test_embeddings.py  # Embeddings system test
├─ ask-and-open.sh     # Convenience script for testing
├─ OPENAI_SETUP.md     # OpenAI integration guide
├─ .env.example
└─ README.md
```

## Next steps (your v1 path)
- ✅ **AI-powered SQL generation** - Implemented with OpenAI and LangChain
- ✅ **HTML visualization** - Beautiful charts and tables
- ✅ **Embeddings infrastructure** - ChromaDB setup for intelligent context
- ✅ **Caching system** - Query caching with TTL
- 🔄 **Schema embeddings** - Use embeddings to enhance AI prompts (Step 2)
- 🔄 **Question embeddings** - Learn from query patterns (Step 3)
- 🔄 **User feedback** - Collect feedback to improve responses (Step 4)
- 🔄 **SQL error correction** - Catch and fix SQL errors automatically
- 🔄 **Advanced chart types** - Extend beyond bar/line charts
- 🔄 **Performance optimization** - Add pagination and result limiting

## Security
- Use a **read-only** DB user for the API.
- Sanitize and/or restrict SQL (only SELECT by default).
- Limit rows/columns in responses; paginate for large results.




## NL–SQL Agent: Master Checklist

### MVP (Minmum Viable Product)
- [ ] FastAPI app with `/ask`, `/schema`, `/healthz`
- [ ] SQLAlchemy connection + MySQL 8 seed (db/init.sql)
- [ ] NL → SQL draft (rule-based/LLM stub), execute, return rows

### Schema memory + recovery
- [ ] `describe_schema()` and `search_schema()` over embedded docs
- [ ] Retry loop on SQL errors (introspect → fix → rerun)
- [ ] Guardrails: read-only user, block DDL/DML, LIMIT defaults

### Charts + caching
- [ ] Plotly chart builders (`charts.py`) + optional `chart_json` in responses
- [ ] Simple cache (LRU/sqlite) keyed by (question, schema_version)

### Tests + Docker
- [ ] Unit tests for intents (top-N, date windows, grouping)
- [ ] E2E goldens (monthly sales 6m; top 10 products last quarter)
- [ ] `docker-compose.yml` for MySQL; happy-path script/Makefile

### Polish
- [ ] README: Quick start, Reference (Data model, Endpoints, Layout)
- [ ] `.env.example` + `.env.template` (DB URLs matrix)
- [ ] Pre-commit (black, isort, ruff, pytest)

---

License: MIT
