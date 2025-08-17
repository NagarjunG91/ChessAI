# LLM Configuration for CrewAI Agents

This guide shows you how to configure different Large Language Models (LLMs) for your CrewAI chess analytics agents.

## 🚀 **Quick Start**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (choose one):
   ```bash
   # For OpenAI
   export OPENAI_API_KEY="your-openai-key-here"
   
   # For Anthropic Claude
   export ANTHROPIC_API_KEY="your-anthropic-key-here"
   
   # For Google Gemini
   export GOOGLE_API_KEY="your-google-key-here"
   ```

3. **Choose your LLM** in `main.py`:
   ```python
   LLM_PROVIDER = "openai"  # Change to: "anthropic", "gemini", or "ollama"
   ```

## 🤖 **Available LLM Options**

### **1. OpenAI (Default)**
- **Models**: GPT-4, GPT-3.5-turbo
- **Cost**: Pay-per-token
- **Quality**: Excellent
- **Setup**: Requires `OPENAI_API_KEY`

### **2. Anthropic Claude**
- **Models**: Claude-3-Sonnet, Claude-3-Haiku
- **Cost**: Pay-per-token
- **Quality**: Excellent, very safe
- **Setup**: Requires `ANTHROPIC_API_KEY`

### **3. Google Gemini**
- **Models**: Gemini Pro, Gemini Pro Vision
- **Cost**: Pay-per-token
- **Quality**: Very good
- **Setup**: Requires `GOOGLE_API_KEY`

### **4. Local Models (Ollama)**
- **Models**: Llama2, Mistral, CodeLlama
- **Cost**: Free (runs locally)
- **Quality**: Good to very good
- **Setup**: Requires Ollama installed locally

## 🔧 **Configuration Examples**

### **OpenAI Setup:**
```bash
export OPENAI_API_KEY="sk-..."
# In main.py: LLM_PROVIDER = "openai"
```

### **Claude Setup:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# In main.py: LLM_PROVIDER = "anthropic"
```

### **Gemini Setup:**
```bash
export GOOGLE_API_KEY="AIza..."
# In main.py: LLM_PROVIDER = "gemini"
```

### **Local Ollama Setup:**
```bash
# Install Ollama first: https://ollama.ai/
ollama pull llama2
# In main.py: LLM_PROVIDER = "ollama"
```

## 💡 **LLM Selection Guide**

- **Best Quality**: OpenAI GPT-4 or Claude-3-Sonnet
- **Best Value**: OpenAI GPT-3.5-turbo
- **Most Private**: Local Ollama models
- **Fastest**: Claude-3-Haiku or local models
- **Cheapest**: Local models (free)

## 🧪 **Testing Your Setup**

Run the agents to test your LLM configuration:

```bash
python main.py --user slowbluesman
```

You should see:
- ✅ Using [provider] LLM for CrewAI agents
- Or ⚠️ Could not initialize [provider] LLM. Using CrewAI default.

## 🔒 **Security Notes**

- Never commit API keys to version control
- Use environment variables or `.env` files
- Consider using local models for sensitive data
- Monitor API usage and costs

## 🆘 **Troubleshooting**

**"No API key found" error:**
- Check environment variable is set
- Restart your terminal after setting the key
- Verify the key is valid

**"Could not initialize LLM" error:**
- Check internet connection
- Verify API key permissions
- Try a different provider

**Local models not working:**
- Ensure Ollama is installed and running
- Check if the model is downloaded: `ollama list`
- Try pulling the model: `ollama pull llama2` 