"""
Data processing and storage modules.

This package contains modules for caching, result processing,
schema indexing, and database tools.
"""

from .cache import get_cache, set_cache
from .result_processor import (
    create_result_dictionary,
    generate_chart_from_rows,
    generate_simple_chart_from_rows,
)
from .schema_index import (
    find_similar_questions,
    find_similar_schema,
    get_embedding_stats,
    initialize_schema_embeddings,
    store_question_embedding,
)
from .tools import (
    export_to_csv,
    get_schema_metadata,
    render_chart,
    respond,
    run_sql,
    to_jsonable,
)

__all__ = [
    "get_cache",
    "set_cache",
    "generate_chart_from_rows",
    "generate_simple_chart_from_rows",
    "create_result_dictionary",
    "find_similar_questions",
    "find_similar_schema",
    "store_question_embedding",
    "get_embedding_stats",
    "initialize_schema_embeddings",
    "get_schema_metadata",
    "respond",
    "run_sql",
    "to_jsonable",
    "export_to_csv",
    "render_chart",
]
