import os
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional

import numpy as np
import plotly.graph_objects as go
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/sales"
)

_engine: Optional[Engine] = None


def _engine_once() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def describe_schema() -> Dict[str, Any]:
    """Return basic table/column info (portable across MySQL)."""
    eng = _engine_once()
    with eng.connect() as conn:
        tables = conn.execute(text("SHOW TABLES")).fetchall()
        out = {}
        for (tname,) in tables:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {tname}")).fetchall()
            out[tname] = [
                {
                    "Field": c[0],
                    "Type": c[1],
                    "Null": c[2],
                    "Key": c[3],
                    "Default": c[4],
                    "Extra": c[5],
                }
                for c in cols
            ]
        return out


def get_schema_metadata() -> Dict[str, Any]:
    return {"database_url": DATABASE_URL, "schema": describe_schema()}


def run_sql(sql: str) -> List[Dict[str, Any]]:
    # Simple safety: only allow SELECT by default
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed in this demo.")
    eng = _engine_once()
    with eng.connect() as conn:
        res = conn.execute(text(sql))
        cols = res.keys()
        rows = [dict(zip(cols, row)) for row in res.fetchall()]
        return rows


def render_chart(
    rows: List[Dict[str, Any]],
    spec: Optional[Dict[str, Any]] = None,
    x_key: Optional[str] = None,
    y_key: Optional[str] = None,
) -> Dict[str, Any]:
    spec = spec or {"type": "bar"}
    if not rows or len(rows) == 0:
        return {}

    # If x_key and y_key are provided, use them; otherwise use heuristic
    if x_key and y_key:
        pass  # Use provided keys
    else:
        # Heuristic: if first column is a label and second is numeric → bar
        keys = list(rows[0].keys())
        x_key = keys[0]
        y_key = keys[1] if len(keys) > 1 else None
        if y_key is None:
            return {}

    # Extract data for plotting
    x_data = [row[x_key] for row in rows]
    y_data = [row[y_key] for row in rows]

    # Create figure using lower-level Plotly API
    fig = go.Figure()

    if spec.get("type") == "line":
        fig.add_trace(go.Scatter(x=x_data, y=y_data, mode="lines+markers", name=y_key))
    else:
        fig.add_trace(go.Bar(x=x_data, y=y_data, name=y_key))

    # Update layout
    fig.update_layout(
        title=f"{y_key} by {x_key}",
        xaxis_title=x_key,
        yaxis_title=y_key,
        showlegend=False,
    )

    return fig.to_dict()


def to_jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.generic,)):
        return x.item()
    if isinstance(x, Decimal):
        return float(x)
    if isinstance(x, Mapping):
        return {k: to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [to_jsonable(v) for v in x]
    return x


def respond(payload):
    return jsonable_encoder(payload)  # use for all returns
