# Pytest Coverage Guide

This document explains how to run pytest with coverage analysis for your NL-SQL agent project. Coverage analysis helps you understand which parts of your code are tested and which parts need more test coverage.

## What is Code Coverage?

**Code coverage** measures how much of your source code is executed when your tests run. It helps you:
- Identify untested code
- Ensure your tests cover critical functionality
- Maintain high code quality
- Find dead code

## Basic Coverage Commands

### **1. Simple Coverage:**
```bash
pytest --cov=app
```

### **2. Coverage with Report:**
```bash
pytest --cov=app --cov-report=html
```

### **3. Coverage with Terminal Report:**
```bash
pytest --cov=app --cov-report=term-missing
```

### **4. Coverage with Both HTML and Terminal:**
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## Advanced Coverage Options

### **5. Coverage with Specific Threshold:**
```bash
pytest --cov=app --cov-fail-under=80
```

### **6. Coverage for Specific Files:**
```bash
pytest --cov=app.main --cov=app.agent
```

### **7. Coverage with Branch Coverage:**
```bash
pytest --cov=app --cov-branch
```

### **8. Coverage with XML Report (for CI/CD):**
```bash
pytest --cov=app --cov-report=xml
```

## Configuration Options

### **pytest.ini Configuration:**
```ini
[tool:pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
testpaths = tests
python_files = test_*.py
```

Then just run:
```bash
pytest
```

### **pyproject.toml Configuration:**
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=html --cov-report=term-missing"
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/venv/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

## Coverage Report Types

### **HTML Report:**
- **Command:** `--cov-report=html`
- **Location:** `htmlcov/index.html`
- **Open:** `open htmlcov/index.html` (macOS) or `start htmlcov/index.html` (Windows)
- **Features:** Interactive, clickable, shows line-by-line coverage

### **Terminal Report:**
- **Command:** `--cov-report=term-missing`
- **Features:** Shows coverage percentage and missing lines in terminal
- **Example Output:**
```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
app/main.py             45      2    96%   23, 45
app/agent.py            78      5    94%   12-15, 67
app/tools.py            56      3    95%   34, 89, 102
--------------------------------------------------
TOTAL                  179     10    94%
```

### **XML Report:**
- **Command:** `--cov-report=xml`
- **Location:** `coverage.xml`
- **Use Case:** CI/CD systems, automated reporting

## Project-Specific Commands

### **For Your NL-SQL Agent:**

#### **Quick Coverage Check:**
```bash
pytest --cov=app --cov-report=term-missing
```

#### **Full Coverage Report:**
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-branch
```

#### **Coverage with Minimum Threshold:**
```bash
pytest --cov=app --cov-fail-under=70 --cov-report=html
```

#### **Coverage for Specific Modules:**
```bash
pytest --cov=app.main --cov=app.agent --cov=app.tools --cov-report=html
```

#### **Coverage for Core Components:**
```bash
pytest --cov=app.agent --cov=app.tools --cov=app.schema_index --cov-report=html
```

## Enhanced Test Script

### **Updated run_tests.py:**
```python
import pytest
import os
import sys

if __name__ == "__main__":
    # Add the 'app' directory to sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Run pytest with coverage
    pytest.main([
        "-v", 
        "-s", 
        "--asyncio-mode=auto",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-branch",
        "--cov-fail-under=70",
        "tests/"
    ])
```

## Coverage Analysis

### **Understanding Coverage Reports:**

#### **Statement Coverage:**
- Measures which statements are executed
- Most basic form of coverage
- Shows percentage of lines executed

#### **Branch Coverage:**
- Measures which branches (if/else) are executed
- More thorough than statement coverage
- Use `--cov-branch` flag

#### **Function Coverage:**
- Measures which functions are called
- Shows percentage of functions tested

#### **Class Coverage:**
- Measures which classes are instantiated
- Shows percentage of classes tested

### **Coverage Thresholds:**

#### **Recommended Thresholds:**
- **Minimum:** 70% (acceptable for most projects)
- **Good:** 80% (good coverage)
- **Excellent:** 90% (excellent coverage)
- **Perfect:** 100% (all code tested)

#### **Setting Thresholds:**
```bash
# Fail if coverage is below 80%
pytest --cov=app --cov-fail-under=80

# Fail if coverage is below 90%
pytest --cov=app --cov-fail-under=90
```

## Coverage Best Practices

### **1. Focus on Critical Code:**
```bash
# Test core functionality first
pytest --cov=app.agent --cov=app.tools
```

### **2. Exclude Non-Critical Code:**
```python
# In your code, mark lines to exclude
def __repr__(self):  # pragma: no cover
    return f"User({self.id})"
```

### **3. Use Branch Coverage:**
```bash
# Always use branch coverage for thorough testing
pytest --cov=app --cov-branch
```

### **4. Regular Coverage Checks:**
```bash
# Run coverage regularly during development
pytest --cov=app --cov-report=term-missing
```

## Troubleshooting

### **Common Issues:**

#### **1. Coverage Not Working:**
```bash
# Install pytest-cov if not installed
pip install pytest-cov

# Check if it's installed
pytest --version
```

#### **2. Import Errors:**
```bash
# Make sure you're in the project root
cd /path/to/nl-sql-agent

# Run with Python path
PYTHONPATH=. pytest --cov=app
```

#### **3. Missing Coverage Data:**
```bash
# Clear coverage data and run again
coverage erase
pytest --cov=app
```

#### **4. Slow Coverage:**
```bash
# Run coverage only on specific modules
pytest --cov=app.main --cov=app.agent
```

## CI/CD Integration

### **GitHub Actions Example:**
```yaml
name: Tests with Coverage
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests with coverage
      run: |
        pytest --cov=app --cov-report=xml --cov-fail-under=80
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### **Coverage Badge:**
Add coverage badge to your README:
```markdown
[![Coverage](https://codecov.io/gh/yourusername/nl-sql-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/nl-sql-agent)
```

## Coverage Commands Summary

### **Most Useful Commands:**

1. **Quick Check:** `pytest --cov=app --cov-report=term-missing`
2. **Full Report:** `pytest --cov=app --cov-report=html --cov-report=term-missing`
3. **With Threshold:** `pytest --cov=app --cov-fail-under=80 --cov-report=html`
4. **Branch Coverage:** `pytest --cov=app --cov-branch --cov-report=html`

### **For Your Project:**
```bash
# Recommended command for your NL-SQL agent
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-branch --cov-fail-under=70
```

This command will:
- Run all tests
- Generate HTML coverage report
- Show terminal coverage report
- Include branch coverage
- Fail if coverage is below 70%

## Next Steps

1. **Run Coverage:** Start with basic coverage to see current state
2. **Set Threshold:** Set a reasonable coverage threshold (70-80%)
3. **Improve Coverage:** Add tests for uncovered code
4. **Monitor Regularly:** Run coverage checks regularly
5. **CI Integration:** Add coverage to your CI/CD pipeline

Coverage analysis is essential for maintaining code quality and ensuring your NL-SQL agent is thoroughly tested! 🎯
