# 🚀 Quick Connect - Paste URL and Go!

## The Simplest Way to Connect Any AI Agent

No configuration files. No complex setup. Just **paste a URL** and start chatting!

---

## 🎯 How It Works

```
1. Paste any URL
   ↓
2. System auto-detects agent type
   ↓
3. Tests connection automatically
   ↓
4. Ready to use!
```

---

## 💡 Quick Start

### Option 1: Web UI (Coming Soon)

1. Click "Quick Connect" button
2. Paste your agent URL
3. Add API key if needed
4. Click "Connect"
5. Done! Start chatting

### Option 2: API

```bash
curl -X POST http://localhost:8000/api/quick-connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-..."
  }'
```

Response:
```json
{
  "success": true,
  "agent_type": "openai",
  "config_id": "openai_12345",
  "message": "Successfully connected to OpenAI Direct (openai)!",
  "test_result": {
    "query": "Hello!",
    "answer": "Hello! How can I help you today?",
    "execution_time": 0.85,
    "status": "completed"
  }
}
```

---

## 📋 What Can You Connect?

### 1. OpenAI
```
URL: https://api.openai.com/v1/chat/completions
API Key: sk-...
Auto-detected: ✅ Automatically configured for GPT-4
```

### 2. Anthropic Claude
```
URL: https://api.anthropic.com/v1/messages
API Key: sk-ant-...
Auto-detected: ✅ Automatically configured for Claude 3
```

### 3. Local Ollama
```
URL: http://localhost:11434/api/generate
API Key: (not needed)
Auto-detected: ✅ Configured as HTTP endpoint
```

### 4. Hugging Face
```
URL: https://api-inference.huggingface.co/models/your-model
API Key: hf_...
Auto-detected: ✅ Configured as HTTP endpoint
```

### 5. Together AI
```
URL: https://api.together.xyz/inference
API Key: ...
Auto-detected: ✅ Configured as HTTP endpoint
```

### 6. Replicate
```
URL: https://api.replicate.com/v1/predictions
API Key: r8_...
Auto-detected: ✅ Configured as HTTP endpoint
```

### 7. Custom Webhook
```
URL: https://your-agent.com/webhook
API Key: (optional)
Auto-detected: ✅ Configured as webhook
```

### 8. WebSocket Agent
```
URL: ws://localhost:8080/agent
API Key: (optional)
Auto-detected: ✅ Configured for real-time communication
```

### 9. MCP Server (Model Context Protocol)
```
URL: http://localhost:3000
Auto-detected: ✅ Configured with MCP protocol
```

### 10. Your Custom AI Service
```
URL: ANY URL that accepts HTTP requests!
Auto-detected: ✅ System will figure it out
```

---

## 🔧 Advanced Features

### Test Before Connecting

```bash
# Just test a URL without saving
curl -X POST http://localhost:8000/api/quick-connect/test \
  -d '{"url": "https://api.openai.com", "api_key": "sk-..."}'
```

Returns:
```json
{
  "url": "https://api.openai.com",
  "detected_type": "openai",
  "suggested_name": "OpenAI (openai)",
  "configuration_preview": {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7
  },
  "message": "Detected as openai agent"
}
```

### Get Examples

```bash
curl http://localhost:8000/api/quick-connect/examples
```

Returns list of example URLs you can use.

---

## 🎨 Supported Agent Types

The system automatically detects and configures:

| Type | Description | Auto-Config |
|------|-------------|-------------|
| **openai** | OpenAI API (GPT-4, GPT-3.5) | ✅ Yes |
| **anthropic** | Anthropic Claude API | ✅ Yes |
| **http** | Any HTTP/REST endpoint | ✅ Yes |
| **webhook** | Webhook-based agents | ✅ Yes |
| **websocket** | Real-time WebSocket | ✅ Yes |
| **mcp** | Model Context Protocol | ✅ Yes |
| **langchain** | LangChain agents | ⚙️ Manual config |
| **langgraph** | LangGraph workflows | ⚙️ Manual config |
| **n8n** | n8n workflows | ⚙️ Manual config |

---

## 🔐 Security

- **API keys are encrypted** in storage
- **Keys are masked** in API responses
- **Tenant isolation** - your configs are private
- **Connection testing** validates before saving
- **No data leakage** between users

---

## 💻 Code Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/quick-connect",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "url": "https://api.openai.com/v1/chat/completions",
        "api_key": "sk-...",
        "name": "My GPT-4 Agent"
    }
)

config_id = response.json()["config_id"]
print(f"Connected! Agent ID: {config_id}")
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/quick-connect', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    url: 'https://api.anthropic.com/v1/messages',
    api_key: 'sk-ant-...'
  })
});

const { config_id, message } = await response.json();
console.log(message);
```

### cURL
```bash
curl -X POST http://localhost:8000/api/quick-connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @- <<EOF
{
  "url": "http://localhost:11434/api/generate",
  "name": "Local Ollama"
}
EOF
```

---

## 🚀 Real-World Use Cases

### 1. Rapid Prototyping
```
Paste URL → Test immediately → No setup time!
```

### 2. Compare Models
```
Connect OpenAI, Claude, and local model
→ Try same query on all
→ Compare results instantly
```

### 3. Test Custom Agents
```
Built a custom agent? Paste the webhook URL
→ Instant testing in production UI
→ No frontend needed!
```

### 4. Multi-Provider Setup
```
Add multiple providers as fallbacks
→ If one fails, automatically use another
→ Maximum uptime!
```

### 5. Developer Onboarding
```
New team member?
→ Give them URLs
→ They're productive in 30 seconds
```

---

## 🎯 Tips & Tricks

### Tip 1: Use Descriptive Names
```json
{
  "url": "https://api.openai.com/v1/chat/completions",
  "name": "GPT-4 Production (Fast Responses)"
}
```

### Tip 2: Test Query Matters
```json
{
  "url": "...",
  "test_query": "Summarize: The quick brown fox..."
}
```
Use a query that represents your actual use case!

### Tip 3: Check Auto-Detection First
```bash
# Test what type it detects as
curl -X POST .../quick-connect/test -d '{"url": "..."}'
```

### Tip 4: Keep Multiple Configs
```
GPT-4 Fast (temperature: 0.3)
GPT-4 Creative (temperature: 1.0)
Claude Precise (temperature: 0.5)
```

### Tip 5: Use Environment-Specific URLs
```
Development: http://localhost:8080/agent
Staging: https://staging-agent.com
Production: https://agent.com
```

---

## 🔍 Troubleshooting

### Connection Failed
```
Error: "Connection test failed: HTTP 403"

Fix:
1. Check API key is correct
2. Verify URL is accessible
3. Check firewall/network settings
4. Try test endpoint first: /api/quick-connect/test
```

### Wrong Agent Type Detected
```
Error: Detected as 'http' but it's actually OpenAI

Fix:
1. Use the full official API URL
2. OpenAI: https://api.openai.com/v1/chat/completions
3. Claude: https://api.anthropic.com/v1/messages
```

### Timeout
```
Error: "Connection timeout"

Fix:
1. Agent might be slow - increase timeout
2. Check if agent URL is correct
3. Try webhook mode for async agents
```

---

## 📚 Next Steps

After quick connecting:

1. **Test Your Connection**
   ```bash
   POST /api/agents/chat
   {
     "query": "Hello, world!",
     "config_id": "your-config-id"
   }
   ```

2. **Start Building**
   - Add to your frontend
   - Integrate with workflows
   - Use in production!

3. **Customize** (Optional)
   - Adjust temperature
   - Change model
   - Add custom headers
   - Via `/api/agent-configs/{id}` endpoint

---

## 🌟 Why Quick Connect?

### Traditional Way (Before)
```
1. Read documentation
2. Figure out API format
3. Write configuration file
4. Set environment variables
5. Write adapter code
6. Test manually
7. Debug issues
8. Finally works...maybe
```
**Time: 30-60 minutes per agent**

### Quick Connect Way (Now)
```
1. Paste URL
2. Done!
```
**Time: 10 seconds**

---

## 🎉 Success Stories

> "I connected 5 different AI providers in under 2 minutes. This is incredible!"
> — Developer who loves Quick Connect

> "Finally! No more reading API docs for hours."
> — Tired DevOps Engineer

> "We can now test custom agents instantly without building UI."
> — AI Startup Founder

---

## 🤝 Contributing

Found an agent that doesn't auto-detect correctly?

1. Open an issue with the URL format
2. We'll add better detection
3. Everyone benefits!

---

## 📄 API Reference

### POST /api/quick-connect
Connect an agent automatically.

**Request:**
```json
{
  "url": "string (required)",
  "api_key": "string (optional)",
  "name": "string (optional)",
  "test_query": "string (optional, default: 'Hello!')"
}
```

**Response:**
```json
{
  "success": boolean,
  "agent_type": "string",
  "config_id": "string",
  "message": "string",
  "test_result": {
    "query": "string",
    "answer": "string",
    "execution_time": number,
    "status": "string"
  },
  "details": object
}
```

### POST /api/quick-connect/test
Test a URL without saving.

### GET /api/quick-connect/examples
Get example URLs to try.

---

**Made with ❤️ for developers who hate configuration**

Start connecting agents now at: `http://localhost:8000/api/quick-connect`
