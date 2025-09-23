# NL-SQL Agent System Design

## Architecture Overview

This document provides a comprehensive system design diagram and explanation for the NL-SQL Agent project.

## System Architecture Diagram

```mermaid
graph TB
    %% User Interface Layer
    subgraph "User Interface Layer"
        WEB[Web Browser]
        API[REST API Endpoints]
    end

    %% Application Layer
    subgraph "Application Layer"
        FASTAPI[FastAPI Application<br/>app/main.py]
        AGENT[AI Agent<br/>app/agent.py]
        TOOLS[Database Tools<br/>app/tools.py]
        CHARTS[Chart Generation<br/>app/charts.py]
        MODELS[Data Models<br/>app/models.py]
    end

    %% AI/ML Layer
    subgraph "AI/ML Layer"
        OPENAI[OpenAI GPT-4<br/>LLM Integration]
        LANGCHAIN[LangChain Framework<br/>Chain Management]
        CHROMADB[ChromaDB<br/>Vector Database]
        SCHEMA_IDX[Schema Index<br/>app/schema_index.py]
    end

    %% Data Layer
    subgraph "Data Layer"
        MYSQL[(MySQL Database<br/>Sales Data)]
        CACHE[In-Memory Cache<br/>app/cache.py]
        EMBEDDINGS[Schema Embeddings<br/>Vector Storage]
    end

    %% Infrastructure Layer
    subgraph "Infrastructure Layer"
        DOCKER[Docker Containers]
        UVICORN[Uvicorn ASGI Server]
        VOLUMES[Docker Volumes<br/>Data Persistence]
    end

    %% External Services
    subgraph "External Services"
        OPENAI_API[OpenAI API<br/>GPT-4 Endpoint]
    end

    %% Data Flow Connections
    WEB --> API
    API --> FASTAPI
    FASTAPI --> AGENT
    AGENT --> OPENAI
    AGENT --> LANGCHAIN
    AGENT --> SCHEMA_IDX
    SCHEMA_IDX --> CHROMADB
    CHROMADB --> EMBEDDINGS
    AGENT --> TOOLS
    TOOLS --> MYSQL
    TOOLS --> CACHE
    AGENT --> CHARTS
    CHARTS --> WEB
    FASTAPI --> UVICORN
    UVICORN --> DOCKER
    MYSQL --> VOLUMES
    CHROMADB --> VOLUMES
    OPENAI --> OPENAI_API

    %% Styling
    classDef userLayer fill:#e1f5fe
    classDef appLayer fill:#f3e5f5
    classDef aiLayer fill:#fff3e0
    classDef dataLayer fill:#e8f5e8
    classDef infraLayer fill:#fce4ec
    classDef externalLayer fill:#fff8e1

    class WEB,API userLayer
    class FASTAPI,AGENT,TOOLS,CHARTS,MODELS appLayer
    class OPENAI,LANGCHAIN,CHROMADB,SCHEMA_IDX aiLayer
    class MYSQL,CACHE,EMBEDDINGS dataLayer
    class DOCKER,UVICORN,VOLUMES infraLayer
    class OPENAI_API externalLayer
```

## Component Details

### 1. User Interface Layer
- **Web Browser**: Frontend interface for user interaction
- **REST API**: HTTP endpoints for programmatic access

### 2. Application Layer
- **FastAPI Application**: Main web framework handling HTTP requests
- **AI Agent**: Core intelligence for SQL generation and query processing
- **Database Tools**: SQL execution, connection management, and data retrieval
- **Chart Generation**: Data visualization using Plotly
- **Data Models**: Pydantic models for data validation and serialization

### 3. AI/ML Layer
- **OpenAI GPT-4**: Large language model for natural language understanding
- **LangChain Framework**: Orchestrates AI workflows and prompt management
- **ChromaDB**: Vector database for semantic search and schema embeddings
- **Schema Index**: Manages database schema vectorization and learning

### 4. Data Layer
- **MySQL Database**: Primary data storage for sales information
- **In-Memory Cache**: Performance optimization for frequent queries
- **Schema Embeddings**: Vector representations of database schema

### 5. Infrastructure Layer
- **Docker Containers**: Containerized deployment and isolation
- **Uvicorn ASGI Server**: High-performance Python web server
- **Docker Volumes**: Persistent data storage

## Data Flow Process

### 1. Query Processing Flow
```
User Question → FastAPI → AI Agent → OpenAI GPT-4
                ↓
            Schema Index → ChromaDB → Schema Embeddings
                ↓
            Database Tools → MySQL → Query Results
                ↓
            Chart Generation → Plotly → HTML Visualization
                ↓
            Web Browser ← Response
```

### 2. Learning Flow
```
Successful Queries → Schema Index → ChromaDB
                ↓
            Vector Embeddings → Similarity Search
                ↓
            Enhanced Prompts → Better SQL Generation
```

### 3. Caching Flow
```
Query Request → Cache Check → Hit/Miss
                ↓
            Miss → Database Query → Cache Store
                ↓
            Hit → Return Cached Result
```

## Key Features

### 1. **Intelligent SQL Generation**
- Natural language to SQL conversion
- Context-aware query generation
- Error correction and fallback mechanisms

### 2. **Adaptive Learning System**
- Schema vectorization for better context
- Query pattern recognition
- Performance metrics and analytics

### 3. **Interactive Visualization**
- Automatic chart type detection
- Responsive HTML generation
- Export functionality (CSV)

### 4. **Performance Optimization**
- Connection pooling
- Query result caching
- Database indexing

### 5. **Scalability Features**
- Containerized deployment
- Horizontal scaling capability
- Persistent data storage

## Security Considerations

- **API Authentication**: Token-based authentication
- **SQL Injection Prevention**: Parameterized queries
- **Data Validation**: Pydantic model validation
- **Container Isolation**: Docker security boundaries

## Monitoring and Observability

- **Health Checks**: `/health` endpoint
- **Performance Metrics**: Query execution times
- **Error Logging**: Structured error tracking
- **Learning Analytics**: Success/failure rates

## Deployment Architecture

```mermaid
graph LR
    subgraph "Production Environment"
        LB[Load Balancer]
        APP1[App Instance 1]
        APP2[App Instance 2]
        DB[(MySQL Cluster)]
        VECTOR[(ChromaDB)]
    end
    
    LB --> APP1
    LB --> APP2
    APP1 --> DB
    APP2 --> DB
    APP1 --> VECTOR
    APP2 --> VECTOR
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **AI/ML**: OpenAI GPT-4, LangChain, ChromaDB
- **Database**: MySQL 8.0
- **Visualization**: Plotly
- **Infrastructure**: Docker, Docker Compose
- **Server**: Uvicorn ASGI server
- **Caching**: In-memory Python cache
- **Validation**: Pydantic

## Future Enhancements

- **Multi-database Support**: PostgreSQL, SQLite compatibility
- **Advanced Analytics**: Machine learning insights
- **Real-time Updates**: WebSocket support
- **API Versioning**: Semantic versioning
- **Advanced Caching**: Redis integration
- **Monitoring**: Prometheus/Grafana integration
