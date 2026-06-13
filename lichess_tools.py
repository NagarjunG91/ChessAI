from http.client import HTTPException
import httpx
from crewai.tools import tool


LICHESS_API = "https://lichess.org/api"

@tool("get_lichess_perfs")
async def get_lichess_perfs(username: str) -> dict:
    """Fetch user performance stats from Lichess API."""
    url = f"{LICHESS_API}/user/{username}"
    data = await fetch_lichess(url)
    perfs = data.get('perfs', {})
    return perfs

@tool("get_lichess_rating_history")
async def get_lichess_rating_history(username: str) -> dict:
    """Fetch user rating history from Lichess API."""
    url = f"{LICHESS_API}/user/{username}/rating-history"
    data = await fetch_lichess(url)
    return data

@tool("get_lichess_performance")
async def get_lichess_performance(username: str, performance_type: str) -> dict:
    """Read performance statistics of a user, for a single performance typefrom Lichess API."""
    url = f"{LICHESS_API}/user/{username}/perf/{performance_type}"
    data = await fetch_lichess(url)
    return data

async def fetch_lichess(url, headers=None):
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json() if 'application/json' in r.headers.get('content-type', '') else r.text
        return data
