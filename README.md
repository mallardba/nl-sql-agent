# Natural Language to SQL Agent

An intelligent AI-powered system that converts natural language questions into SQL queries, executes them against MySQL databases, and returns structured data with interactive visualizations.

## Overview

This application leverages OpenAI's GPT models to understand natural language queries and generate accurate SQL statements. It features intelligent error correction, adaptive learning capabilities, and comprehensive data visualization through interactive charts and tables.

**Key Features:**
- **AI-Powered SQL Generation** - Converts natural language to SQL using OpenAI GPT-4
- **Interactive Data Visualization** - Dynamic charts (bar, line, pie, scatter, area) with Plotly
- **Intelligent Error Correction** - Automatic SQL error detection and correction
- **Adaptive Learning System** - Learns from query patterns using ChromaDB embeddings
- **Query Caching** - Performance optimization with intelligent caching
- **Comprehensive Testing** - Full test suite with pytest and CI/CD integration

---

## Initial Setup

### Prerequisites
- Python 3.13+
- MySQL 8.0+ (local install or Docker)
- OpenAI API key

### 1. Environment Configuration

```bash
# Clone and setup environment
git clone <repository-url>
cd nl-sql-agent
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and OpenAI API key
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/sales

# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

### 2. Database Setup

**Option A: Docker (Recommended)**
```bash
# Start MySQL container
docker compose up -d db

# Load schema and seed data
mysql -h 127.0.0.1 -P 3306 -u root -proot sales < db/init.sql
```

**Option B: Existing MySQL Server**
```bash
# Create database and load schema
mysql -u your_username -p
CREATE DATABASE sales;
USE sales;
SOURCE db/init.sql;
```

### 3. OpenAI Integration

```bash
# Run setup script (automated)
python scripts/setup/setup_openai.py

# Or manually configure in .env file
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

### 4. Embeddings Setup (Optional but Recommended)

```bash
# Start all services including ChromaDB
docker compose up -d

# Initialize schema embeddings (one-time setup)
curl -X POST http://localhost:8000/embeddings/initialize

# Verify setup
python test_embeddings.py
```

### 5. Development Tools (Optional)

```bash
# Install development dependencies
pip install -r requirements-dev.txt
pre-commit install

# Run tests to verify setup
pytest
```

---

## Normal Operation

### Starting the Service

```bash
# Production server
python scripts/server/start_server.py

# Development server with auto-reload
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Making Queries

**JSON Response (API)**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 products by revenue last quarter?"}'
```

**HTML Response (Web Interface)**
```bash
curl -X POST "http://localhost:8000/ask?html=true" \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 products by revenue last quarter?"}'
```

**Browser Testing**
```bash
# Direct browser access
http://localhost:8000/ask-html?question=sales%20by%20month

# Convenience script
./scripts/ask/ask-and-open.sh "sales by month"
```

### Response Formats

**JSON Response Structure:**
```json
{
  "answer_text": "Here are the top 5 products by revenue for Q2 FY2025.",
  "sql": "SELECT p.product_name, SUM(oi.quantity*oi.unit_price) AS revenue...",
  "rows": [
    {"product_name": "Widget A", "revenue": 12345.67},
    {"product_name": "Widget B", "revenue": 9876.54}
  ],
  "chart_json": { "plotly chart specification" }
}
```

**HTML Response Features:**
- Interactive charts with Plotly
- Formatted data tables
- Responsive design for mobile/desktop
- Export functionality

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Natural language to SQL conversion |
| `/ask?html=true` | POST | HTML response with charts and tables |
| `/ask-html?question=...` | GET | Browser-friendly HTML interface |
| `/test-html` | GET | Test HTML generation without database |
| `/schema` | GET | Database schema metadata |
| `/health` | GET | Service health check |
| `/embeddings/status` | GET | Embeddings system status |
| `/embeddings/initialize` | POST | Initialize schema embeddings |
| `/learning/metrics` | GET | Learning metrics and performance stats |
| `/learning/clear` | POST | Clear all learning metrics |
| `/learning/dashboard` | GET | HTML learning metrics dashboard |
| `/errors/logs` | GET | Recent AI error logs |
| `/errors/summary` | GET | Error summary and statistics |
| `/errors/stats` | GET | Log file statistics |
| `/errors/clear` | POST | Clear all error logs |
| `/export/csv` | POST | Export query results as CSV |

---

## Database Management

### Schema Overview

The application includes a comprehensive e-commerce schema with:

**Core Tables:**
- `customers`, `employees`, `regions`, `channels`
- `categories`, `products`, `product_tags`, `inventories`
- `promotions`, `orders`, `order_items`, `payments`
- `shipments`, `returns`

**Views:**
- `v_product_revenue` - Product revenue calculations
- `v_monthly_sales` - Monthly sales aggregations
- `v_customer_ltv` - Customer lifetime value

**Helper Functions:**
- `fiscal_quarter(date)` - Fiscal year calculations (FY starts April)

### Updating Database Schema

**Adding New Tables:**
1. Update `db/init.sql` with new table definitions
2. Reload schema: `mysql -h 127.0.0.1 -P 3306 -u root -proot sales < db/init.sql`
3. Reinitialize embeddings: `curl -X POST http://localhost:8000/embeddings/initialize`

**Modifying Existing Tables:**
1. Create migration script in `db/migrations/`
2. Apply changes to database
3. Update embeddings if schema structure changed
4. Run tests to verify compatibility

**Adding Seed Data:**
1. Add INSERT statements to `db/init.sql`
2. Reload database: `mysql -h 127.0.0.1 -P 3306 -u root -proot sales < db/init.sql`
3. Test with sample queries

### Database Connection Options

| Environment | Connection String |
|-------------|------------------|
| Docker | `mysql+pymysql://root:root@localhost:3306/sales` |
| Local MySQL | `mysql+pymysql://username:password@127.0.0.1:3306/sales` |
| AWS RDS | `mysql+pymysql://admin:secret@mydb.abcdefghij.us-west-2.rds.amazonaws.com:3306/sales` |
| Azure MySQL | `mysql+pymysql://user@myserver:password@myserver.mysql.database.azure.com:3306/sales` |

---

## Architecture

### Project Structure
```
nl-sql-agent/
├── app/
│   ├── main.py          # FastAPI application and routes
│   ├── agent.py         # AI-powered SQL generation
│   ├── tools.py         # SQL execution and utilities
│   ├── charts.py        # Data visualization components
│   ├── schema_index.py  # ChromaDB embeddings system
│   ├── cache.py         # Query caching implementation
│   └── models.py        # Pydantic data models
├── db/
│   └── init.sql         # Database schema and seed data
├── tests/
│   ├── test_end_to_end.py
│   └── test_sql_generation.py
├── requirements.txt
├── docker-compose.yml
└── README.md
```

### Key Components

**AI Agent (`app/agent.py`)**
- OpenAI GPT-4 integration for SQL generation
- Context-aware prompting with schema embeddings
- Error detection and correction mechanisms

**Visualization (`app/charts.py`)**
- Plotly-powered interactive charts
- Intelligent chart type selection
- Responsive HTML generation

**Learning System (`app/schema_index.py`)**
- ChromaDB vector database integration
- Query pattern learning and categorization
- Performance metrics tracking

**Caching (`app/cache.py`)**
- In-memory query result caching
- TTL-based cache invalidation
- Performance optimization

---

## Security Considerations

- **Database Access**: Use read-only database users for production
- **SQL Injection**: All queries are generated by AI with parameterized inputs
- **API Security**: Implement rate limiting and authentication for production use
- **Data Privacy**: Ensure sensitive data is properly masked in responses

---

## Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Verify MySQL is running
docker ps | grep mysql

# Test connection
mysql -h 127.0.0.1 -P 3306 -u root -proot -e "SELECT 1"
```

**OpenAI API Errors:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API access
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Embeddings Issues:**
```bash
# Check ChromaDB status
curl http://localhost:8000/embeddings/status

# Reinitialize if needed
curl -X POST http://localhost:8000/embeddings/initialize
```

### Performance Optimization

- **Caching**: Enable query caching for repeated requests
- **Database Indexing**: Add indexes for frequently queried columns
- **Result Limiting**: Implement pagination for large result sets
- **Connection Pooling**: Configure SQLAlchemy connection pooling

---

## License

MIT License - see LICENSE file for details.