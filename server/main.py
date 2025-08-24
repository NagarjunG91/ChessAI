from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the agents directory to the path so we can import the agent classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
from agents.main import DataAgent, AnalyticsAgent, NarrativeAgent, UIAgent

app = FastAPI(title="ChessMCP Lichess MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS middleware

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    narrative_agent = NarrativeAgent()
    response = await narrative_agent.run(req.message)
    return {"response": response}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LICHESS_API = "https://lichess.org/api"
CACHE_TTL = 60  # seconds
cache = TTLCache(maxsize=100, ttl=CACHE_TTL)

class UserProfile(BaseModel):
    id: str
    username: str
    perfs: dict
    createdAt: int
    seenAt: int
    profile: dict = None
    title: str = None
    patron: bool = None
    verified: bool = None
    # ... add more fields as needed

class UserStats(BaseModel):
    bullet: dict = None
    blitz: dict = None
    rapid: dict = None
    classical: dict = None
    puzzle: dict = None
    correspondence: dict = None
    # ... add more fields as needed

class RatingHistory(BaseModel):
    name: str
    points: list

class GameMetadata(BaseModel):
    id: str
    createdAt: int
    lastMoveAt: int
    turns: int
    winner: str = None
    players: dict
    opening: dict = None
    status: str
    # ... add more fields as needed

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_lichess(url, headers=None):
    if url in cache:
        return cache[url]
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json() if 'application/json' in r.headers.get('content-type', '') else r.text
        cache[url] = data
        return data

@app.get("/user/{username}/profile")
async def get_user_profile(username: str):
    url = f"{LICHESS_API}/user/{username}"
    data = await fetch_lichess(url)
    return data

@app.get("/user/{username}/stats")
async def get_user_stats(username: str):
    url = f"{LICHESS_API}/user/{username}"
    data = await fetch_lichess(url)
    perfs = data.get('perfs', {})
    stats = {k: v for k, v in perfs.items() if k in ['bullet', 'blitz', 'rapid', 'classical', 'puzzle', 'correspondence']}
    return stats

@app.get("/user/{username}/history")
async def get_user_history(username: str):
    url = f"{LICHESS_API}/user/{username}/rating-history"
    data = await fetch_lichess(url)
    return data

@app.get("/user/{username}/games")
async def get_user_games(username: str, max_games: int = 10):
    url = f"{LICHESS_API}/games/user/{username}?max={max_games}&opening=true&clocks=false&evals=false&perfType=all"
    headers = {"Accept": "application/x-ndjson"}
    if url in cache:
        return cache[url]
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        # Parse NDJSON
        games = [httpx.Response(200, content=line).json() for line in r.text.strip().split('\n') if line]
        cache[url] = games
        return games

@app.get("/user/{username}/dashboard")
async def get_user_dashboard(username: str):
    """Get complete processed dashboard data including CrewAI insights"""
    try:
        # Run the agent pipeline in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            # Run the agent pipeline with a timeout
            dashboard = await asyncio.wait_for(
                loop.run_in_executor(executor, _run_agent_pipeline, username),
                timeout=30.0  # 30 second timeout
            )
        return dashboard
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Dashboard generation timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing dashboard: {str(e)}")

def _run_agent_pipeline(username):
    """Run the CrewAI agent pipeline in a separate thread"""
    try:
        # Initialize agents
        data_agent = DataAgent()
        analytics_agent = AnalyticsAgent()
        narrative_agent = NarrativeAgent()
        ui_agent = UIAgent()
        
        # Run the agent pipeline
        data = data_agent.run(username)
        analytics = analytics_agent.run(data)
        insights = narrative_agent.run(analytics, data)
        dashboard = ui_agent.run(data, analytics, insights)
        
        return dashboard
    except Exception as e:
        raise Exception(f"Agent pipeline error: {str(e)}") 
