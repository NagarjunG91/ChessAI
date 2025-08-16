# ChessMCP: Lichess-Integrated MCP Server & Dashboard

## Overview
A professional chess analytics platform powered by FastMCP, CrewAI multi-agent system, and a modern React dashboard. Integrates with Lichess for real-time user stats, rating history, and insights.

---

## Project Structure

- `server/`   — FastAPI MCP backend (Lichess integration, caching, retry)
- `agents/`   — CrewAI multi-agent system (Data, Analytics, Narrative, UI agents)
- `client/`   — React dashboard (Tailwind, shadcn/ui, Recharts, Framer Motion)
- `run.py`    — Starter script for orchestrating agents and server

---

## Setup Instructions

### 1. Backend & Agents
```bash
cd MCPServer
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
pip install -r agents/requirements.txt
```

### 2. Frontend
```bash
cd client
npm install
npm run start
```

### 3. Running the System
```bash
# Start the MCP server
cd server
uvicorn main:app --reload

# Run CrewAI agents
cd ../agents
python main.py --user <lichess_username>

# Or use the starter script
python run.py --user <lichess_username>
```

---

## Example Lichess API Query
- Profile: `https://lichess.org/api/user/<username>`
- Stats:   `https://lichess.org/api/user/<username>/perf/{bullet,blitz,rapid,...}`
- Games:   `https://lichess.org/api/games/user/<username>?max=10&opening=true`

---

## Features
- **MCP Server**: Modular endpoints for profile, stats, history, games. Caching + retry logic.
- **CrewAI Agents**: Data, Analytics, Narrative, UI agents orchestrated for insights and dashboard.
- **Dashboard**: Modern, responsive UI with charts, tables, and insights.

---

## License
MIT 