# ChessAI Agentic App

A minimal agentic AI app using CrewAI, OpenAI, to analyze Lichess user performance.

## Features
- Reads Lichess user perfs via API
- Uses CrewAI agent to analyze and give an opinion

## Setup
1. Install dependencies:
   ```sh
   uv pip install requirements.txt
   ```
2. Set your OpenAI API key or azure opena ai:
   ```sh
   export OPENAI_API_KEY=your-key-here
   ```
3. Run the app:
   ```python3 agent.py
   ```

