# Natural-Language SQL Analyst (Agentic AI)

Turn plain English questions into SQL for **MySQL**, execute them, and return **tables + charts**.
This starter includes a minimal **FastAPI** service, agent stubs (prompting + tools), schema indexing,
and test scaffolding you can extend.

## Quick start

### 1) Setup environment
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DB creds and LLM key (if using one)

# Optional dev tools setup
pip install -r requirements-dev.txt
```

### 2) Run MySQL (optional, via Docker)
```bash
docker compose up -d db
# (re)load comprehensive schema + seed data
mysql -h 127.0.0.1 -P 3306 -u root -proot sales < db/init.sql
```

### 3) Run tests (optional)
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

## Data model overview
- Rich schema: `customers`, `employees`, `regions`, `channels`, `categories`, `products`, `product_tags`, `inventories`, `promotions`, `orders`, `order_items`, `payments`, `shipments`, `returns`.
- Views: `v_product_revenue`, `v_monthly_sales`, `v_customer_ltv`.
- Helper: `fiscal_quarter(date)` (FY starts in April).
- Seed data spans 2024–2025 with cancellations, discounts, returns, multi-payments.

## Endpoints
- `POST /ask` → `{ question }` -> `{ answer_text, sql, rows, chart_json? }`
- `GET  /schema` → schema metadata
- `GET  /healthz` → health check

## Project layout
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
│  ├─ test_sql_generation.py
│  └─ test_end_to_end.py
├─ requirements.txt
├─ docker-compose.yml
├─ .env.example
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
