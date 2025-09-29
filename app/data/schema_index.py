"""
Schema Embeddings & Learning System

Provides intelligent context-aware SQL generation using ChromaDB vector embeddings.
Features schema vectorization, query pattern learning, and similarity search for
enhanced AI prompts. Includes comprehensive learning metrics and performance tracking.

Key Features:
- Schema embeddings for context-aware AI prompts
- Query pattern learning and categorization  
- Similarity search for related questions
- Learning metrics dashboard with performance analytics
- Error pattern recognition and success tracking
"""

import hashlib
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

# Initialize ChromaDB client
_chroma_client = None
_schema_collection = None
_questions_collection = None


def _get_chroma_client():
    """Get or create ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        # Use persistent storage in Docker path or local fallback
        persist_directory = (
            "/app/data/chroma_db"
            if os.path.exists("/app/data/chroma_db")
            else os.path.join(os.getcwd(), "data", "chroma_db")
        )
        _chroma_client = chromadb.PersistentClient(
            path=persist_directory, settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def _get_schema_collection():
    """Get or create schema collection."""
    global _schema_collection
    if _schema_collection is None:
        client = _get_chroma_client()
        try:
            _schema_collection = client.get_collection("schema_embeddings")
        except (ValueError, Exception):
            _schema_collection = client.create_collection(
                name="schema_embeddings",
                metadata={"description": "Database schema embeddings"},
            )
    return _schema_collection


def _get_questions_collection():
    """Get or create questions collection."""
    global _questions_collection
    if _questions_collection is None:
        client = _get_chroma_client()
        try:
            _questions_collection = client.get_collection("question_embeddings")
        except (ValueError, Exception):
            _questions_collection = client.create_collection(
                name="question_embeddings",
                metadata={"description": "Question and SQL pattern embeddings"},
            )
    return _questions_collection


def create_embedding(text: str) -> List[float]:
    """
    Create embedding for text using a simple hash-based approach.
    This is a placeholder - in production you would use OpenAI embeddings.
    """
    # Simple hash-based embedding for now (hashlib)
    # In production, replace this with OpenAI embeddings

    # Create a hash of the text
    hash_obj = hashlib.md5(text.encode())
    hash_bytes = hash_obj.digest()

    # Convert to a list of floats (normalized to 0-1 range)
    embedding = [float(b) / 255.0 for b in hash_bytes]

    # Use 384 dimensions (common embedding size)
    # Pad or truncate to a consistent length
    while len(embedding) < 384:
        embedding.extend(embedding[: min(len(embedding), 384 - len(embedding))])

    return embedding[:384]


def store_schema_embedding(table_name: str, column_info: List[Dict[str, Any]]):
    """Store table schema information as embedding."""
    # Create descriptive text from schema
    schema_text = f"Table: {table_name}\n"
    for col in column_info:
        schema_text += (
            f"Column: {col['Field']}, Type: {col['Type']}, Key: {col['Key']}\n"
        )

    # Create embedding
    embedding = create_embedding(schema_text)

    # Store in ChromaDB
    collection = _get_schema_collection()
    collection.add(
        embeddings=[embedding],
        documents=[schema_text],
        ids=[f"schema_{table_name}"],
        metadatas=[
            {
                "type": "schema",
                "table_name": table_name,
                "column_count": len(column_info),
            }
        ],
    )


def store_question_embedding(
    question: str, sql: str, metadata: Optional[Dict[str, Any]] = None
):
    """Store question and its SQL as embedding."""
    # Create embedding for the question
    embedding = create_embedding(question)

    # Store in ChromaDB
    collection = _get_questions_collection()
    collection.add(
        embeddings=[embedding],
        documents=[question],
        ids=[f"question_{hash(question)}"],
        metadatas=[
            {
                "type": "question",
                "sql": sql,
                "timestamp": str(os.path.getmtime(__file__)),  # Placeholder timestamp
                **(metadata or {}),
            }
        ],
    )


def find_similar_schema(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Find schema information similar to the query."""
    collection = _get_schema_collection()

    # Create embedding for the query
    query_embedding = create_embedding(query)

    # Search for similar schema
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # Handle case where no results are found
    if not results["documents"] or not results["documents"][0]:
        return []

    return [
        {"document": doc, "metadata": meta or {}, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0] if results["metadatas"] else [],
            results["distances"][0] if results["distances"] else [],
        )
    ]


def find_similar_questions(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Find questions similar to the query."""
    collection = _get_questions_collection()

    # Create embedding for the query
    query_embedding = create_embedding(query)

    # Search for similar questions
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # Handle case where no results are found
    if not results["documents"] or not results["documents"][0]:
        return []

    return [
        {
            "question": doc,
            "sql": meta.get("sql", "") if meta else "",
            "metadata": meta or {},
            "distance": dist,
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0] if results["metadatas"] else [],
            results["distances"][0] if results["distances"] else [],
        )
    ]


def initialize_schema_embeddings(schema_info: Dict[str, Any]):
    """Initialize schema embeddings from database schema."""
    print("Initializing schema embeddings...")

    for table_name, columns in schema_info.get("schema", {}).items():
        store_schema_embedding(table_name, columns)
        print(f"✅ Stored embedding for table: {table_name}")

    print("Schema embeddings initialized!")


def get_embedding_stats() -> Dict[str, Any]:
    """Get statistics about stored embeddings."""
    schema_collection = _get_schema_collection()
    questions_collection = _get_questions_collection()

    return {
        "schema_embeddings": schema_collection.count(),
        "question_embeddings": questions_collection.count(),
        "collections": ["schema_embeddings", "question_embeddings"],
    }
