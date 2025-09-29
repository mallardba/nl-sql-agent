# Enum Objects vs Enum Values

## Overview

This document explains the difference between enum objects (`ChartType.BAR`) and enum values (`ChartType.BAR.value`) in our SQL Agent system, and when to use each.

## The Difference

### **Enum Object: `ChartType.BAR`**
- **Type**: `ChartType` enum instance
- **Value**: The actual enum object
- **Usage**: Type checking, comparisons, IDE autocomplete
- **Example**: `if chart_type == ChartType.BAR:`

### **Enum Value: `ChartType.BAR.value`**
- **Type**: `str`
- **Value**: `"bar"`
- **Usage**: JSON serialization, API responses, database storage
- **Example**: `{"type": ChartType.BAR.value}` → `{"type": "bar"}`

## Why We Use `.value` in Our Codebase

### **1. JSON Serialization**
```python
# ✅ This works - returns {"type": "bar"}
chart_json = {"type": ChartType.BAR.value}

# ❌ This would fail - enum objects aren't JSON serializable
chart_json = {"type": ChartType.BAR}  # TypeError: Object of type ChartType is not JSON serializable
```

### **2. API Responses**
```python
# FastAPI needs string values for JSON responses
result = {
    "chart_type": ChartType.BAR.value,  # ✅ "bar"
    "sql_source": SQLSource.AI.value,  # ✅ "ai"
    "error_type": ErrorType.SQL_EXECUTION_ERROR.value,  # ✅ "sql_execution_error"
}
```

### **3. Database Storage**
```python
# Databases expect primitive types, not enum objects
db_record = {
    "chart_type": ChartType.BAR.value,  # ✅ "bar"
    "query_category": QueryCategory.ANALYTICS.value,  # ✅ "analytics"
}
```

### **4. External Libraries**
```python
# Plotly expects string chart types
fig = go.Figure(data=go.Bar(x=x_data, y=y_data))
chart_type = ChartType.BAR.value  # ✅ "bar"
```

## When to Use Each

### **Use Enum Objects (`ChartType.BAR`)**

#### **Comparisons**
```python
def process_chart(chart_type: ChartType):
    if chart_type == ChartType.BAR:
        return "Processing bar chart"
    elif chart_type == ChartType.LINE:
        return "Processing line chart"
```

#### **Type Hints**
```python
def create_result_dictionary(
    sql_source: SQLSource,
    chart_type: ChartType,
    error_type: ErrorType
) -> Dict[str, Any]:
    # Function signature uses enum types for type safety
```

#### **IDE Autocomplete**
```python
# IDE shows all available options
chart_type = ChartType.  # Shows: BAR, LINE, PIE, SCATTER, AREA
```

### **Use Enum Values (`ChartType.BAR.value`)**

#### **JSON Serialization**
```python
import json

data = {
    "chart_type": ChartType.BAR.value,
    "sql_source": SQLSource.AI.value
}
json_string = json.dumps(data)  # ✅ Works
```

#### **API Responses**
```python
from fastapi import FastAPI

@app.get("/chart")
def get_chart():
    return {
        "type": ChartType.BAR.value,  # ✅ "bar"
        "data": [1, 2, 3, 4]
    }
```

#### **Configuration Files**
```python
# config.py
DEFAULT_CHART_TYPE = ChartType.BAR.value  # ✅ "bar"
```

#### **External System Integration**
```python
# When calling external APIs that expect strings
external_api_call({
    "chart_type": ChartType.BAR.value,  # ✅ "bar"
    "data_source": SQLSource.AI.value   # ✅ "ai"
})
```

## Examples from Our Codebase

### **Chart Generation**
```python
# app/query_utils.py
def determine_chart_type(...) -> str:
    if condition:
        return ChartType.BAR.value  # ✅ Returns "bar"
    else:
        return ChartType.LINE.value  # ✅ Returns "line"
```

### **Result Processing**
```python
# app/result_processor.py
result = {
    "sql_source": sql_source.value,  # ✅ "ai", "heuristic", etc.
    "chart_json": chart_json,
    "query_category": category.value  # ✅ "analytics", "revenue", etc.
}
```

### **Error Handling**
```python
# app/agent.py
error_details = {
    "type": ErrorType.SQL_EXECUTION_ERROR.value,  # ✅ "sql_execution_error"
    "message": str(error)
}
```

## Best Practices

### **1. Use Enum Objects for Logic**
```python
def handle_sql_source(sql_source: SQLSource):
    if sql_source == SQLSource.AI:
        return "AI generated"
    elif sql_source == SQLSource.HEURISTIC:
        return "Heuristic generated"
```

### **2. Use Enum Values for Serialization**
```python
def serialize_result(result: Dict[str, Any]) -> str:
    return json.dumps({
        "sql_source": result["sql_source"].value,  # ✅ Convert to string
        "chart_type": result["chart_type"].value
    })
```

### **3. Convert When Needed**
```python
def process_request(data: Dict[str, Any]):
    # Convert string to enum for type safety
    try:
        sql_source = SQLSource(data["sql_source"])
    except ValueError:
        sql_source = SQLSource.ERROR
    
    # Use enum for logic
    if sql_source == SQLSource.AI:
        # Process AI logic
        pass
```

## Summary

- **`ChartType.BAR`** = Type-safe enum object for logic and comparisons
- **`ChartType.BAR.value`** = String value for serialization and external systems
- **Use enums for type safety** in function parameters and internal logic
- **Use `.value` for JSON, APIs, databases** and external integrations
- **Convert between them** as needed for different contexts

This approach gives us the best of both worlds: type safety internally and compatibility with external systems.
