import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from langfuse import observe, get_client

load_dotenv()

DEFAULT_USER = os.getenv("DEFAULT_LICHESS_USER", "slowbluesman")
LICHESS_API = "https://lichess.org/api"

mcp = FastMCP("Lichess Chess Coach")
langfuse = get_client()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def fetch(url: str) -> dict | list | str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Accept": "application/json"})
        r.raise_for_status()
        return r.json() if "application/json" in r.headers.get("content-type", "") else r.text


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
@observe(name="get_lichess_perfs")
async def get_lichess_perfs(username: str = DEFAULT_USER) -> dict:
    """Get all performance stats (ratings across all formats) for a Lichess player."""
    data = await fetch(f"{LICHESS_API}/user/{username}")
    return data.get("perfs", {})


@mcp.tool()
@observe(name="get_lichess_rating_history")
async def get_lichess_rating_history(username: str = DEFAULT_USER) -> list:
    """Get the full rating history across all formats for a Lichess player."""
    return await fetch(f"{LICHESS_API}/user/{username}/rating-history")


@mcp.tool()
@observe(name="get_lichess_performance")
async def get_lichess_performance(
    performance_type: str = "blitz",
    username: str = DEFAULT_USER,
) -> dict:
    """
    Get detailed performance stats for a player in one specific format.
    performance_type options: bullet, blitz, rapid, classical, correspondence,
    chess960, kingOfTheHill, threeCheck, antichess, atomic, horde, racingKings, crazyhouse
    """
    return await fetch(f"{LICHESS_API}/user/{username}/perf/{performance_type}")


@mcp.tool()
@observe(name="get_lichess_profile")
async def get_lichess_profile(username: str = DEFAULT_USER) -> dict:
    """Get the full public profile of a Lichess player (bio, title, country, playtime, etc.)."""
    return await fetch(f"{LICHESS_API}/user/{username}")


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("lichess://player/{username}/profile")
@observe(name="resource/player-profile")
async def player_profile_resource(username: str) -> str:
    """Public profile and all performance ratings for a Lichess player."""
    data = await fetch(f"{LICHESS_API}/user/{username}")
    perfs = data.get("perfs", {})
    lines = [f"# Lichess Profile: {username}"]
    if data.get("title"):
        lines.append(f"Title: {data['title']}")
    if data.get("profile", {}).get("bio"):
        lines.append(f"Bio: {data['profile']['bio']}")
    lines.append("\n## Ratings")
    for fmt, stats in perfs.items():
        rating = stats.get("rating")
        games = stats.get("games")
        if games:
            lines.append(f"- {fmt}: {rating} ({games} games)")
    return "\n".join(lines)


@mcp.resource("lichess://player/{username}/rating-history")
@observe(name="resource/rating-history")
async def rating_history_resource(username: str) -> str:
    """Full rating history across all formats for a Lichess player."""
    data = await fetch(f"{LICHESS_API}/user/{username}/rating-history")
    lines = [f"# Rating History: {username}"]
    for entry in data:
        name = entry.get("name", "unknown")
        points = entry.get("points", [])
        if points:
            latest = points[-1]
            lines.append(f"## {name}")
            lines.append(f"Latest: {latest[3]} on {latest[0]}-{latest[1]+1:02d}-{latest[2]:02d}")
            lines.append(f"Total data points: {len(points)}")
    return "\n".join(lines)


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def coach_player(username: str = DEFAULT_USER, format: str = "blitz") -> str:
    """Generate a coaching prompt for a specific player and format."""
    return f"""You are an expert chess coach with 30 years of experience.

Analyse the Lichess player '{username}' for the '{format}' format:
1. Use get_lichess_performance to fetch their {format} stats
2. Use get_lichess_rating_history to see their rating trend over time
3. Identify strengths, weaknesses, and rating trajectory
4. Give 3 specific, actionable improvement recommendations

Be direct and specific. Back every claim with the data you retrieved."""


@mcp.prompt()
def compare_formats(username: str = DEFAULT_USER) -> str:
    """Generate a prompt to compare a player's performance across all formats."""
    return f"""You are an expert chess coach.

For Lichess player '{username}':
1. Use get_lichess_perfs to get all their format ratings
2. Identify which formats they perform best and worst in
3. Explain what this gap reveals about their playing style
4. Recommend which format they should focus on to improve fastest"""


if __name__ == "__main__":
    mcp.run()
