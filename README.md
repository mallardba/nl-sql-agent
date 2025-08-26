# Natural-Language SQL Analyst (Agentic AI)

Turn plain English questions into SQL for **MySQL**, execute them, and return **tables + charts**.
This starter includes a minimal **FastAPI** service, agent stubs (prompting + tools), schema indexing,
and test scaffolding you can extend.

## Quick start

### Note on MySQL
Section 2 (Run MySQL via Docker) is **optional**. You can use Docker Compose to spin up a MySQL 8 instance for convenience, or instead point `DATABASE_URL` to any existing MySQL 8 server (local install, WSL2, VM, or cloud service) where you have loaded `db/init.sql`.

### 1) Setup
- Copy `.env.example` → `.env` and fill in required values (e.g. your LLM API key, which you’ll need once you integrate an LLM).
- If you’re configuring the database, check `.env.template` for ready-made `DATABASE_URL` connection strings. Just copy the appropriate line for your environment (Docker, local install, AWS RDS, etc.) into your `.env`.

```bash
python -m venv .venv && source .venv/bin/activate
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

### 3) Run all tests (optional)
```bash
pytest
```

### 4) Launch API
```bash
uvicorn app.main:app --reload --port 8000
```

### 5) Try it
```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Top 5 products by revenue last quarter?"}'
```



## Reference


### Data model overview
- Rich schema: `customers`, `employees`, `regions`, `channels`, `categories`, `products`, `product_tags`, `inventories`, `promotions`, `orders`, `order_items`, `payments`, `shipments`, `returns`.
- Views: `v_product_revenue`, `v_monthly_sales`, `v_customer_ltv`.
- Helper: `fiscal_quarter(date)` (FY starts in April).
- Seed data spans 2024–2025 with cancellations, discounts, returns, multi-payments.

### Endpoints
- `POST /ask` → `{ question }` -> `{ answer_text, sql, rows, chart_json? }`
- `GET  /schema` → schema metadata
- `GET  /healthz` → health check


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
│  ├─ agent.py         # Agent orchestration (LLM/tool loop) - stubbed
│  ├─ tools.py         # SQL execution, schema lookup, chart tool
│  ├─ prompts.py       # System + few-shot prompts
│  ├─ charts.py        # Plotly chart builders
│  ├─ schema_index.py  # Build/search schema embedding (stubbed)
│  ├─ cache.py         # Simple query cache
│  └─ models.py        # Pydantic models
├─ db/
│  └─ init.sql         # Example schema + seed data
├─ tests/
│  ├─ conftest.py
│  ├─ test_ask_endpoint.py
│  ├─ test_healthz.py
│  ├─ test_schema_loaded.py
│  ├─ test_sql_generation.py
│  └─ test_end_to_end.py
├─ requirements.txt
|─ requirements-dev.txt
|─ pytest.ini
├─ docker-compose.yml
├─ .env.example
|─ .env.template
└─ README.md
```

## Next steps (your v1 path)
- Implement NL→SQL in `agent.py` (LangChain or hand-rolled ReAct loop).
- Flesh out `schema_index.py` to vectorize schema docs and support lookups.
- Add error-recovery: catch SQL errors, refine query, retry safely.
- Add caching & pagination; extend chart specs beyond simple bar/line.
- Write real tests with a small, reproducible dataset in `db/init.sql`.

## Security
- Use a **read-only** DB user for the API.
- Sanitize and/or restrict SQL (only SELECT by default).
- Limit rows/columns in responses; paginate for large results.

---

License: MIT
