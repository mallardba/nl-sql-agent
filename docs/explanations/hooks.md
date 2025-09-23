# Understanding Different Types of Hooks

This document explains three different types of "hooks" commonly used in software development: **Git Commit Hooks**, **Web Hooks**, and **React Hooks**. While they share the same name, they serve very different purposes in the development ecosystem.

## Git Commit Hooks

**Git hooks** are scripts that run automatically at certain points in the Git workflow. They allow you to customize Git's behavior and enforce project standards.

### What are Git Hooks?

Git hooks are executable scripts that Git runs automatically when certain events occur. They're stored in the `.git/hooks/` directory and can be written in any scripting language (bash, Python, etc.).

### Types of Git Hooks:

#### **Pre-Commit Hook:**
Runs before a commit is created. Used for:
- **Code formatting** (black, prettier)
- **Linting** (flake8, eslint)
- **Testing** (pytest, jest)
- **Security checks** (bandit, safety)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run linting
flake8 app/
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Run tests
pytest tests/
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "Pre-commit checks passed!"
```

#### **Pre-Push Hook:**
Runs before pushing to remote repository. Used for:
- **Integration tests**
- **Build verification**
- **Documentation checks**

```bash
#!/bin/bash
# .git/hooks/pre-push

# Run full test suite
pytest tests/ --cov=app
if [ $? -ne 0 ]; then
    echo "Tests failed. Push aborted."
    exit 1
fi

# Check documentation
python -m pydoc app.main
if [ $? -ne 0 ]; then
    echo "Documentation check failed. Push aborted."
    exit 1
fi
```

#### **Commit Message Hook:**
Validates commit message format:

```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Format: type(scope): description"
    echo "Types: feat, fix, docs, style, refactor, test, chore"
    exit 1
fi
```

### Setting Up Git Hooks:

#### **Manual Setup:**
```bash
# Make hook executable
chmod +x .git/hooks/pre-commit

# Test the hook
.git/hooks/pre-commit
```

#### **Using pre-commit Framework:**
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

# Install hooks
pre-commit install
```

### Benefits of Git Hooks:

1. **Code Quality** - Enforce coding standards
2. **Automation** - Run checks automatically
3. **Consistency** - Ensure all commits meet standards
4. **Error Prevention** - Catch issues before they reach the repository

### In Your Project Context:

```bash
# Example pre-commit hook for your NL-SQL agent
#!/bin/bash

# Format code with black
black app/ tests/

# Lint with flake8
flake8 app/ tests/

# Type check with mypy
mypy app/

# Run tests
pytest tests/ -v

# Check if all checks passed
if [ $? -eq 0 ]; then
    echo "✅ All pre-commit checks passed!"
else
    echo "❌ Pre-commit checks failed!"
    exit 1
fi
```

## Web Hooks

**Web hooks** are HTTP callbacks that allow applications to send real-time notifications to other applications when specific events occur.

### What are Web Hooks?

Web hooks are user-defined HTTP callbacks triggered by events. When an event occurs, the source application makes an HTTP request to the web hook URL with event data.

### How Web Hooks Work:

```
1. Event occurs in Source App
2. Source App sends HTTP POST to Web Hook URL
3. Target App receives and processes the data
4. Target App responds with status code
```

### Common Web Hook Examples:

#### **GitHub Web Hooks:**
```python
# Flask endpoint to receive GitHub web hooks
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    # Verify GitHub signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return 'Unauthorized', 401
    
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type == 'push':
        # Handle push event
        handle_push_event(payload)
    elif event_type == 'pull_request':
        # Handle PR event
        handle_pr_event(payload)
    
    return 'OK', 200

def verify_signature(payload, signature):
    secret = 'your-webhook-secret'
    expected = 'sha256=' + hmac.new(
        secret.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

#### **Payment Web Hooks (Stripe):**
```python
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'your-webhook-secret'
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_successful_payment(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_failed_payment(payment_intent)
    
    return 'OK', 200
```

#### **Database Change Web Hooks:**
```python
# PostgreSQL trigger web hook
import psycopg2
from psycopg2.extras import RealDictCursor

def create_change_webhook():
    conn = psycopg2.connect("postgresql://user:pass@localhost/db")
    cur = conn.cursor()
    
    # Create function to call web hook
    cur.execute("""
        CREATE OR REPLACE FUNCTION notify_webhook()
        RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify('data_change', 
                json_build_object(
                    'table', TG_TABLE_NAME,
                    'action', TG_OP,
                    'old', row_to_json(OLD),
                    'new', row_to_json(NEW)
                )::text
            );
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    cur.execute("""
        CREATE TRIGGER data_change_trigger
        AFTER INSERT OR UPDATE OR DELETE ON users
        FOR EACH ROW EXECUTE FUNCTION notify_webhook();
    """)
    
    conn.commit()
    cur.close()
    conn.close()
```

### Web Hook Security:

#### **Signature Verification:**
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

#### **Rate Limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def webhook_endpoint():
    # Handle web hook
    pass
```

### Web Hook Best Practices:

1. **Verify Signatures** - Always verify web hook authenticity
2. **Idempotency** - Handle duplicate events gracefully
3. **Rate Limiting** - Prevent abuse
4. **Error Handling** - Return appropriate HTTP status codes
5. **Logging** - Log all web hook events
6. **Retry Logic** - Implement retry mechanisms

### In Your Project Context:

```python
# Web hook for your NL-SQL agent to notify about query patterns
@app.route('/webhook/query-patterns', methods=['POST'])
def query_pattern_webhook():
    payload = request.json
    
    # Extract query pattern data
    pattern_type = payload.get('type')  # 'successful', 'failed', 'optimized'
    query = payload.get('query')
    execution_time = payload.get('execution_time')
    
    # Store pattern for learning
    if pattern_type == 'successful':
        schema_index.add_successful_pattern(query, execution_time)
    elif pattern_type == 'failed':
        schema_index.add_failed_pattern(query, payload.get('error'))
    
    return 'Pattern recorded', 200
```

## React Hooks

**React hooks** are functions that let you use state and other React features in functional components. They were introduced in React 16.8.

### What are React Hooks?

React hooks are special functions that start with "use" and allow you to "hook into" React features like state and lifecycle methods from functional components.

### Basic React Hooks:

#### **useState Hook:**
```javascript
import React, { useState } from 'react';

function Counter() {
    const [count, setCount] = useState(0);
    
    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={() => setCount(count + 1)}>
                Increment
            </button>
        </div>
    );
}
```

#### **useEffect Hook:**
```javascript
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        // Fetch user data when component mounts or userId changes
        fetch(`/api/users/${userId}`)
            .then(response => response.json())
            .then(data => {
                setUser(data);
                setLoading(false);
            });
    }, [userId]); // Dependency array
    
    if (loading) return <div>Loading...</div>;
    
    return (
        <div>
            <h1>{user.name}</h1>
            <p>{user.email}</p>
        </div>
    );
}
```

#### **useContext Hook:**
```javascript
import React, { createContext, useContext } from 'react';

// Create context
const ThemeContext = createContext();

// Provider component
function ThemeProvider({ children }) {
    const [theme, setTheme] = useState('light');
    
    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

// Consumer component
function ThemedButton() {
    const { theme, setTheme } = useContext(ThemeContext);
    
    return (
        <button 
            style={{ 
                backgroundColor: theme === 'light' ? '#fff' : '#333',
                color: theme === 'light' ? '#333' : '#fff'
            }}
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        >
            Toggle Theme
        </button>
    );
}
```

### Custom Hooks:

#### **useSQLQuery Hook:**
```javascript
import { useState, useEffect } from 'react';

function useSQLQuery(question) {
    const [sql, setSql] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        if (!question) return;
        
        setLoading(true);
        setError(null);
        
        fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        })
        .then(response => response.json())
        .then(data => {
            setSql(data.sql);
            setLoading(false);
        })
        .catch(err => {
            setError(err.message);
            setLoading(false);
        });
    }, [question]);
    
    return { sql, loading, error };
}

// Usage in component
function SQLGenerator() {
    const [question, setQuestion] = useState('');
    const { sql, loading, error } = useSQLQuery(question);
    
    return (
        <div>
            <input 
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question..."
            />
            {loading && <p>Generating SQL...</p>}
            {error && <p>Error: {error}</p>}
            {sql && <pre>{sql}</pre>}
        </div>
    );
}
```

#### **useLocalStorage Hook:**
```javascript
function useLocalStorage(key, initialValue) {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            return initialValue;
        }
    });
    
    const setValue = (value) => {
        try {
            setStoredValue(value);
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error(error);
        }
    };
    
    return [storedValue, setValue];
}

// Usage
function Settings() {
    const [theme, setTheme] = useLocalStorage('theme', 'light');
    const [language, setLanguage] = useLocalStorage('language', 'en');
    
    return (
        <div>
            <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
            </select>
        </div>
    );
}
```

### React Hooks Rules:

1. **Only call hooks at the top level** - Don't call hooks inside loops, conditions, or nested functions
2. **Only call hooks from React functions** - Call hooks from React function components or custom hooks

### Advanced Hooks:

#### **useReducer Hook:**
```javascript
import React, { useReducer } from 'react';

function reducer(state, action) {
    switch (action.type) {
        case 'increment':
            return { count: state.count + 1 };
        case 'decrement':
            return { count: state.count - 1 };
        case 'reset':
            return { count: 0 };
        default:
            throw new Error();
    }
}

function Counter() {
    const [state, dispatch] = useReducer(reducer, { count: 0 });
    
    return (
        <div>
            <p>Count: {state.count}</p>
            <button onClick={() => dispatch({ type: 'increment' })}>
                +
            </button>
            <button onClick={() => dispatch({ type: 'decrement' })}>
                -
            </button>
            <button onClick={() => dispatch({ type: 'reset' })}>
                Reset
            </button>
        </div>
    );
}
```

### React Hooks vs Class Components:

| Feature | Class Components | React Hooks |
|---------|-----------------|-------------|
| **State** | `this.state` | `useState` |
| **Lifecycle** | `componentDidMount` | `useEffect` |
| **Context** | `Context.Consumer` | `useContext` |
| **Reusability** | HOCs, Render Props | Custom Hooks |
| **Complexity** | Higher | Lower |

### In Your Project Context:

If you were to build a frontend for your NL-SQL agent:

```javascript
// Custom hook for your SQL agent
function useSQLAgent() {
    const [question, setQuestion] = useState('');
    const [sql, setSql] = useState('');
    const [explanation, setExplanation] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const generateSQL = async (query) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: query })
            });
            
            const data = await response.json();
            setSql(data.sql);
            setExplanation(data.explanation);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    return {
        question,
        setQuestion,
        sql,
        explanation,
        loading,
        error,
        generateSQL
    };
}
```

## Summary

While all three types of "hooks" share the same name, they serve very different purposes:

- **Git Commit Hooks** - Automate code quality checks and enforce standards
- **Web Hooks** - Enable real-time communication between applications
- **React Hooks** - Provide state and lifecycle functionality in functional components

Each type of hook is essential in its respective domain and understanding all three gives you a comprehensive toolkit for modern software development! 🚀
