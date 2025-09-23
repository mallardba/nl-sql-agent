# What are Python Type Hints and Type Annotations?

**Python Type Hints** (also called Type Annotations) are a feature introduced in Python 3.5 that allows you to specify the expected data types of variables, function parameters, and return values. While Python remains dynamically typed, type hints provide static type checking capabilities and improve code clarity, maintainability, and developer experience. This document explains what type hints are, why they're essential, and how they power your NL-SQL agent.

## What are Type Hints?

**Type Hints** are annotations that indicate the expected type of a variable, function parameter, or return value. They don't change Python's runtime behavior but provide information for static type checkers, IDEs, and documentation tools.

### The Problem Type Hints Solve:
```python
# Without type hints - Unclear, error-prone
def process_user_data(data):
    name = data['name']  # What type is this?
    age = data['age']    # What type is this?
    email = data['email']  # What type is this?
    
    # These could all fail at runtime
    return f"User {name}, age {age}, email {email}"

# With type hints - Clear, type-safe
def process_user_data(data: dict[str, Any]) -> str:
    name: str = data['name']
    age: int = data['age']
    email: str = data['email']
    
    return f"User {name}, age {age}, email {email}"
```

## What are Type Annotations?

**Type Annotations** are the syntax used to add type hints to Python code. They use the `:` operator to specify types and the `->` operator to specify return types.

### Basic Syntax:
```python
# Variable annotations
name: str = "John"
age: int = 25
is_active: bool = True

# Function annotations
def greet(name: str) -> str:
    return f"Hello, {name}!"

# Class annotations
class User:
    name: str
    age: int
    email: str
```

## Type Hints vs Alternatives:

### **vs Dynamic Typing:**
| Aspect | Dynamic Typing | Type Hints |
|--------|----------------|------------|
| **Runtime Behavior** | No type checking | No runtime checking |
| **Development** | Flexible but error-prone | Structured and safe |
| **IDE Support** | Limited | Excellent |
| **Documentation** | Manual | Automatic |
| **Refactoring** | Risky | Safe |

### **vs Static Typing (Java, C#):**
- **Python**: Optional, gradual adoption, runtime flexibility
- **Static Languages**: Mandatory, compile-time checking, no runtime flexibility

### **vs Documentation Comments:**
```python
# Documentation comments - Manual, not enforced
def process_data(data):
    """
    Process user data.
    
    Args:
        data: Dictionary containing user information
    Returns:
        str: Formatted user string
    """
    return f"User {data['name']}"

# Type hints - Automatic, enforced by tools
def process_data(data: dict[str, Any]) -> str:
    return f"User {data['name']}"
```

## Core Type Hint Features:

### **1. Basic Types:**
```python
from typing import Any, Optional, Union, List, Dict, Tuple

# Basic types
name: str = "John"
age: int = 25
height: float = 5.9
is_active: bool = True

# Collections
names: List[str] = ["John", "Jane", "Bob"]
ages: List[int] = [25, 30, 35]
user_data: Dict[str, Any] = {"name": "John", "age": 25}

# Optional types
email: Optional[str] = None  # Can be str or None
phone: Union[str, int] = "123-456-7890"  # Can be str or int
```

### **2. Function Annotations:**
```python
def calculate_total(items: List[float], tax_rate: float = 0.1) -> float:
    """Calculate total with tax."""
    subtotal = sum(items)
    return subtotal * (1 + tax_rate)

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID, return None if not found."""
    # Implementation here
    return {"id": user_id, "name": "John"} if user_id > 0 else None
```

### **3. Class Annotations:**
```python
class User:
    def __init__(self, name: str, age: int, email: str) -> None:
        self.name: str = name
        self.age: int = age
        self.email: str = email
    
    def get_info(self) -> str:
        return f"{self.name}, {self.age}, {self.email}"
    
    def update_age(self, new_age: int) -> None:
        if new_age > 0:
            self.age = new_age
```

### **4. Generic Types:**
```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        self._items.append(item)
    
    def pop(self) -> T:
        return self._items.pop()
    
    def is_empty(self) -> bool:
        return len(self._items) == 0

# Usage
string_stack: Stack[str] = Stack()
string_stack.push("hello")
string_stack.push("world")

int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
```

## Advanced Type Hint Features:

### **1. Union Types:**
```python
from typing import Union

# Union of multiple types
def process_id(user_id: Union[int, str]) -> str:
    if isinstance(user_id, int):
        return f"User {user_id}"
    else:
        return f"User {user_id}"

# Modern syntax (Python 3.10+)
def process_id(user_id: int | str) -> str:
    if isinstance(user_id, int):
        return f"User {user_id}"
    else:
        return f"User {user_id}"
```

### **2. Optional Types:**
```python
from typing import Optional

def find_user(name: str) -> Optional[User]:
    """Find user by name, return None if not found."""
    # Implementation here
    return User("John", 25, "john@example.com") if name == "John" else None

# Modern syntax (Python 3.10+)
def find_user(name: str) -> User | None:
    return User("John", 25, "john@example.com") if name == "John" else None
```

### **3. Callable Types:**
```python
from typing import Callable, List

def apply_function(numbers: List[int], func: Callable[[int], int]) -> List[int]:
    """Apply function to each number in list."""
    return [func(n) for n in numbers]

# Usage
def square(x: int) -> int:
    return x * x

result = apply_function([1, 2, 3, 4], square)  # [1, 4, 9, 16]
```

### **4. Literal Types:**
```python
from typing import Literal

def process_status(status: Literal["pending", "approved", "rejected"]) -> str:
    """Process status with specific values."""
    if status == "pending":
        return "Processing..."
    elif status == "approved":
        return "Approved!"
    else:
        return "Rejected."

# Only these values are allowed
process_status("pending")    # OK
process_status("approved")   # OK
process_status("invalid")    # Type checker error
```

## Type Hints in Your Project:

### **Your Pydantic Models:**
```python
# From app/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None

class QuestionResponse(BaseModel):
    sql: str
    explanation: str
    execution_time: float
    success: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
```

### **Your FastAPI Endpoints:**
```python
# From app/main.py
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

app = FastAPI()

@app.post("/ask")
def ask_question(request: QuestionRequest) -> QuestionResponse:
    """Ask a question and get SQL response."""
    # Type hints ensure request is QuestionRequest
    # and return value is QuestionResponse
    return QuestionResponse(
        sql="SELECT * FROM users",
        explanation="This query selects all users",
        execution_time=0.123,
        success=True
    )

@app.get("/health")
def health_check() -> HealthResponse:
    """Check application health."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )
```

### **Your Database Tools:**
```python
# From app/tools.py
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional

def run_sql(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute SQL query and return results."""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row) for row in result]

def get_schema() -> Dict[str, List[str]]:
    """Get database schema information."""
    # Implementation here
    return {"users": ["id", "name", "email"], "orders": ["id", "user_id", "total"]}
```

## Benefits of Type Hints:

### **1. IDE Support:**
```python
# IDE provides autocomplete, error detection, and refactoring
def process_user(user: User) -> str:
    return user.name  # IDE knows user has 'name' attribute
```

### **2. Static Type Checking:**
```python
# mypy catches type errors before runtime
def calculate_age(birth_year: int) -> int:
    return 2024 - birth_year

# This would be caught by mypy
result = calculate_age("1990")  # Error: expected int, got str
```

### **3. Documentation:**
```python
# Type hints serve as inline documentation
def create_user(name: str, age: int, email: str) -> User:
    """Create a new user with the given information."""
    return User(name=name, age=age, email=email)
```

### **4. Refactoring Safety:**
```python
# Type checkers ensure refactoring doesn't break type contracts
def process_data(data: Dict[str, Any]) -> List[str]:
    return [str(value) for value in data.values()]

# If you change the return type, type checker will catch all usages
```

## Type Checking Tools:

### **1. mypy:**
```bash
# Install mypy
pip install mypy

# Run type checking
mypy app/

# Configuration in mypy.ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### **2. pyright (Pylance):**
```json
// VS Code settings.json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.autoImportCompletions": true
}
```

### **3. pyre:**
```bash
# Install pyre
pip install pyre-check

# Run type checking
pyre check
```

## Common Type Hint Patterns:

### **1. Database Operations:**
```python
from typing import List, Dict, Any, Optional
from sqlalchemy import Engine

def execute_query(engine: Engine, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute SQL query with parameters."""
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row) for row in result]

def get_table_schema(engine: Engine, table_name: str) -> List[Dict[str, str]]:
    """Get schema information for a table."""
    # Implementation here
    return [{"column": "id", "type": "INTEGER"}, {"column": "name", "type": "VARCHAR"}]
```

### **2. API Responses:**
```python
from typing import Dict, Any, Optional
from datetime import datetime

def create_response(data: Any, success: bool = True, message: str = "") -> Dict[str, Any]:
    """Create standardized API response."""
    return {
        "data": data,
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

def handle_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Handle errors and create error response."""
    return {
        "error": str(error),
        "context": context,
        "success": False,
        "timestamp": datetime.now().isoformat()
    }
```

### **3. Configuration:**
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class AppConfig:
    debug: bool
    database: DatabaseConfig
    openai_api_key: str
    version: str = "1.0.0"
```

## Performance Considerations:

### **Runtime Impact:**
```python
# Type hints have ZERO runtime impact
def process_data(data: List[str]) -> List[str]:
    return [item.upper() for item in data]

# This is identical at runtime to:
def process_data(data):
    return [item.upper() for item in data]
```

### **Import Overhead:**
```python
# Import typing only when needed
from typing import List, Dict, Any, Optional

# Or use modern syntax (Python 3.9+)
def process_data(data: list[str]) -> list[str]:
    return [item.upper() for item in data]
```

## Best Practices:

### **1. Gradual Adoption:**
```python
# Start with function signatures
def calculate_total(items: List[float]) -> float:
    return sum(items)

# Add variable annotations gradually
def process_user_data(data: Dict[str, Any]) -> str:
    name: str = data['name']
    age: int = data['age']
    return f"User {name}, age {age}"
```

### **2. Use Generic Types:**
```python
# Generic functions work with multiple types
def get_first_item(items: List[T]) -> T:
    return items[0]

# Usage
first_string = get_first_item(["a", "b", "c"])  # Returns str
first_int = get_first_item([1, 2, 3])  # Returns int
```

### **3. Avoid Any When Possible:**
```python
# Avoid Any when you can be more specific
def process_data(data: Any) -> Any:  # Too generic
    return data

# Be more specific
def process_data(data: Dict[str, Union[str, int]]) -> str:
    return str(data)
```

## Troubleshooting:

### **Common Issues:**
```python
# Forward references
class User:
    def __init__(self, name: str) -> None:
        self.name = name
        self.friends: List['User'] = []  # Forward reference

# Circular imports
# Use string literals for forward references
def process_user(user: 'User') -> str:
    return user.name
```

### **Type Checker Errors:**
```python
# mypy error: Incompatible types
def add_numbers(a: int, b: int) -> int:
    return a + b

result = add_numbers("1", "2")  # Error: expected int, got str

# Fix: Convert to int
result = add_numbers(int("1"), int("2"))  # OK
```

## Key Benefits for This Project:

1. **Type Safety** - Prevents runtime type errors
2. **IDE Support** - Better autocomplete and error detection
3. **Documentation** - Self-documenting code
4. **Refactoring Safety** - Safe code changes
5. **Team Collaboration** - Clear interfaces and contracts
6. **FastAPI Integration** - Automatic request/response validation
7. **Pydantic Integration** - Data validation and serialization
8. **Maintainability** - Easier to understand and modify code

## Integration with Your AI Agent:

```python
# Your AI agent benefits from type hints by:
# 1. Clear function interfaces
def generate_sql(question: str, schema: Dict[str, List[str]]) -> str:
    """Generate SQL from natural language question."""
    # Implementation here
    return "SELECT * FROM users"

# 2. Type-safe data structures
class QueryContext:
    question: str
    schema: Dict[str, List[str]]
    similar_queries: List[str]
    user_id: Optional[int] = None

# 3. Error handling with types
def execute_sql(query: str) -> Union[List[Dict[str, Any]], str]:
    """Execute SQL query, return results or error message."""
    try:
        # Execute query
        return results
    except Exception as e:
        return f"Error: {str(e)}"

# 4. Configuration with types
@dataclass
class AgentConfig:
    model_name: str
    temperature: float
    max_tokens: int
    timeout: int = 30
```

Type hints are the foundation that makes your Python code more reliable, maintainable, and developer-friendly - they're what enable the type safety and excellent developer experience in your NL-SQL agent! 🚀
