# ChessAI — Lichess MCP Server

An MCP (Model Context Protocol) server that exposes Lichess player data as tools, resources, and prompts — usable directly from Claude Desktop or any MCP-compatible client.

## What's inside

| File | Purpose |
|---|---|
| `lichess_mcp.py` | MCP server — tools, resources, prompts |
| `lichess_tools.py` | Raw Lichess API helpers (used by CrewAI agent) |
| `agent.py` | Standalone CrewAI agent for CLI use |

## MCP Server

### Tools
| Tool | Description |
|---|---|
| `get_lichess_perfs` | All ratings across every format |
| `get_lichess_rating_history` | Full rating timeline |
| `get_lichess_performance` | Detailed stats for one format (bullet, blitz, rapid, etc.) |
| `get_lichess_profile` | Full public profile |

### Resources
- `lichess://player/{username}/profile` — formatted profile card
- `lichess://player/{username}/rating-history` — rating history summary

### Prompts
- `coach_player` — coaching analysis for a player + format
- `compare_formats` — compare performance across all formats

## Setup

1. Clone the repo and create a virtual environment:
   ```sh
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` and fill in your keys:
   ```sh
   cp .env.example .env
   ```

   ```env
   AZURE_API_KEY=your-azure-openai-key
   AZURE_API_BASE=https://your-endpoint.openai.azure.com/
   AZURE_API_VERSION=2024-12-01-preview

   DEFAULT_LICHESS_USER=your-lichess-username

   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://us.cloud.langfuse.com
   ```

## Claude Desktop integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lichess-chess-coach": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/lichess_mcp.py"],
      "env": {
        "DEFAULT_LICHESS_USER": "your-lichess-username"
      }
    }
  }
}
```

Restart Claude Desktop. The tools will be available immediately in any chat.

## Run the MCP inspector (for testing)

```sh
source venv/bin/activate
mcp dev lichess_mcp.py
```

Opens the inspector UI at `http://localhost:6274`.

## Run as a standalone agent (CLI)

```sh
source venv/bin/activate
python3 agent.py
```

## Observability

All tool calls are traced via [Langfuse](https://cloud.langfuse.com) — inputs, outputs, and latency are captured automatically. Set your Langfuse keys in `.env` to enable.
