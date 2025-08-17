"""
LLM Configuration for CrewAI Agents
Choose your preferred LLM by uncommenting the desired option
"""

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

def get_openai_llm():
    """OpenAI GPT models (requires OPENAI_API_KEY)"""
    return ChatOpenAI(
        model="gpt-4",  # or "gpt-3.5-turbo"
        temperature=0.7,
        max_tokens=2000
    )

def get_anthropic_llm():
    """Anthropic Claude models (requires ANTHROPIC_API_KEY)"""
    return ChatAnthropic(
        model="claude-3-sonnet-20240229",  # or "claude-3-haiku-20240307"
        temperature=0.7,
        max_tokens=2000
    )

def get_gemini_llm():
    """Google Gemini models (requires GOOGLE_API_KEY)"""
    return ChatGoogleGenerativeAI(
        model="gemini-pro",  # or "gemini-pro-vision"
        temperature=0.7,
        max_tokens=2000
    )

def get_ollama_llm():
    """Local models via Ollama (requires Ollama running locally)"""
    return Ollama(
        model="llama2",  # or "mistral", "codellama", etc.
        temperature=0.7
    )

def get_llm(provider="openai"):
    """Get LLM instance based on provider preference"""
    
    if provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            return get_openai_llm()
        else:
            print("⚠️  No OPENAI_API_KEY found. Set it in your environment.")
            return None
            
    elif provider == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            return get_anthropic_llm()
        else:
            print("⚠️  No ANTHROPIC_API_KEY found. Set it in your environment.")
            return None
            
    elif provider == "gemini":
        if os.getenv("GOOGLE_API_KEY"):
            return get_gemini_llm()
        else:
            print("⚠️  No GOOGLE_API_KEY found. Set it in your environment.")
            return None
            
    elif provider == "ollama":
        try:
            return get_ollama_llm()
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
            return None
    
    else:
        print(f"⚠️  Unknown provider: {provider}")
        return None

# Usage examples:
# llm = get_llm("openai")      # OpenAI GPT-4
# llm = get_llm("anthropic")   # Claude
# llm = get_llm("gemini")      # Google Gemini
# llm = get_llm("ollama")      # Local models 