# OpenAI Integration Setup Guide

Your NL-SQL agent now supports AI-powered SQL generation using OpenAI! This guide will help you set it up.

## 🚀 Quick Start

### 1. Install Required Packages
```bash
pip install langchain langchain-openai python-dotenv
```

### 2. Get Your OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 3. Configure Environment
Run the setup script:
```bash
python setup_openai.py
```

This will:
- Create a `.env` file if it doesn't exist
- Guide you through API key configuration
- Test the setup

### 4. Add Your API Key
Edit the `.env` file and replace:
```
OPENAI_API_KEY=your-openai-api-key-here
```
with:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## 🔧 How It Works

### Before (Heuristic Rules)
```
Question → Keyword matching → Hard-coded SQL → Results
```

### After (AI-Powered)
```
Question → OpenAI understands intent → Generates SQL → Results
```

### Benefits
- **Smarter**: Understands complex questions
- **Flexible**: Handles questions you haven't programmed for
- **Context-aware**: Uses your database schema intelligently
- **Fallback**: Still works if AI fails (uses original heuristic rules)

## 🧪 Testing

### Test the Integration
```bash
# Start your server
uvicorn app.main:app --reload

# Test with your script
./ask-and-open.sh "What were our top 5 products by revenue last quarter?"
```

### Example Questions to Try
- "Show me sales trends by month"
- "Which customers spent the most money?"
- "What's the average order value by product category?"
- "How many orders did we have last week?"

## 🛠️ Configuration Options

### Environment Variables
```bash
OPENAI_API_KEY=sk-your-key-here          # Required
OPENAI_MODEL=gpt-3.5-turbo              # Optional (default)
OPENAI_TEMPERATURE=0.1                  # Optional (default)
```

### Model Settings
- **`gpt-3.5-turbo`**: Fast, cost-effective (recommended)
- **`gpt-4`**: More accurate, higher cost
- **Temperature**: 0.1 for consistent SQL, 0.7 for creative responses

## 🔒 Security Notes

- **Never commit** your `.env` file to version control
- **Use environment variables** for production deployments
- **Monitor API usage** to control costs
- **Validate SQL** before execution (already implemented)

## 🚨 Troubleshooting

### "LangChain not available"
```bash
pip install langchain langchain-openai python-dotenv
```

### "OpenAI API key not set"
1. Check your `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Restart your application

### "API key invalid"
1. Verify your key starts with `sk-`
2. Check if you have credits in your OpenAI account
3. Ensure the key hasn't expired

### Fallback Mode
If OpenAI fails, your agent automatically falls back to the original heuristic rules, so it will still work!

## 🔮 Next Steps

Once OpenAI is working, you can:
1. **Add more complex prompts** for better SQL generation
2. **Integrate embeddings** for schema understanding
3. **Add conversation memory** for follow-up questions
4. **Implement query validation** and refinement

## 💰 Cost Considerations

- **GPT-3.5-turbo**: ~$0.002 per 1K tokens
- **Typical question**: 100-200 tokens
- **Cost per query**: ~$0.0002-0.0004
- **1000 queries**: ~$0.20-0.40

## 🎯 Advanced Usage

### Custom Prompts
Edit the system prompt in `agent.py` to customize how the AI generates SQL.

### Model Selection
Change `OPENAI_MODEL` in your `.env` file to use different models.

### Temperature Tuning
Adjust `OPENAI_TEMPERATURE` for more/less creative responses.

---

**Need help?** Check the error messages in your terminal - they'll guide you to the solution! 