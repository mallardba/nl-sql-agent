import pytest
from sqlalchemy import create_engine, text

@pytest.mark.asyncio
async def test_database_schema_exists(database_url):
    eng = create_engine(database_url)
    with eng.connect() as conn:
        result = conn.execute(text("SHOW TABLES")).fetchall()
        table_names = {row[0] for row in result}
        expected = {"orders", "order_items", "customers", "products"}
        assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"
