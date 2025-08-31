import httpx
from crewai.tools import tool

@tool("get_lichess_perfs")
def get_lichess_perfs(username: str) -> dict:
    """Fetch user performance stats from Lichess API."""
    url = f"https://lichess.org/api/user/{username}"
    resp = httpx.get(url)
    resp.raise_for_status()
    return resp.json().get("perfs", {})
