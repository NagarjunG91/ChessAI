
import sys
import argparse
import asyncio
import httpx
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
from crewai import Agent, Crew, Task
from llm_config import get_llm
import json

MCP_SERVER = "http://localhost:8000"

# Configure LLM - Change provider here
LLM_PROVIDER = "openai"  # Options: "openai", "anthropic", "gemini", "ollama"
llm = get_llm(LLM_PROVIDER)

if llm is None:
    print(f"⚠️  Could not initialize {LLM_PROVIDER} LLM. Using CrewAI default.")
    llm = None
else:
    print(f"✅ Using {LLM_PROVIDER} LLM for CrewAI agents")

# --- AGENTS ---
class DataAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Data Retrieval Specialist",
            goal="Fetch comprehensive user data from Lichess via MCP server",
            backstory="Expert at gathering chess player statistics, ratings, and game history from Lichess API",
            llm=llm
        )
    
    def run(self, username):
        with httpx.Client() as client:
            profile = client.get(f"{MCP_SERVER}/user/{username}/profile").json()
            stats = client.get(f"{MCP_SERVER}/user/{username}/stats").json()
            history = client.get(f"{MCP_SERVER}/user/{username}/history").json()
            #commenting games for now
            #games = client.get(f"{MCP_SERVER}/user/{username}/games").json()
        return {"profile": profile, "stats": stats, "history": history }

class AnalyticsAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chess Analytics Expert",
            goal="Analyze rating trends, win/loss ratios, and identify strong/weak time controls",
            backstory="Specialist in chess performance analysis with expertise in statistical trends and pattern recognition",
            llm=llm
        )
    
    def run(self, data):
        import numpy as np
        from datetime import datetime, timedelta
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_games = []
        for game in data['games']:
            game_timestamp = game.get('createdAt', 0) / 1000
            game_date = datetime.fromtimestamp(game_timestamp)
            if game_date >= six_months_ago:
                recent_games.append(game)
        trends = {}
        for cat in data['history']:
            if cat['points']:
                recent_points = []
                for point in cat['points']:
                    point_date = datetime(point[0], point[1] + 1, point[2])
                    if point_date >= six_months_ago:
                        recent_points.append(point)
                if len(recent_points) >= 3:
                    ratings = [p[3] for p in recent_points]
                    dates = [i for i in range(len(recent_points))]
                    trend_slope = np.polyfit(dates, ratings, 1)[0]
                    volatility = np.std(ratings)
                    if len(ratings) >= 4:
                        momentum = np.polyfit(dates, ratings, 2)[0] * 2
                    else:
                        momentum = 0
                    if abs(trend_slope) > 2 and volatility < 50:
                        trend_quality = "strong"
                    elif abs(trend_slope) > 1:
                        trend_quality = "moderate"
                    else:
                        trend_quality = "weak"
                    trends[cat['name']] = {
                        'direction': 'upward' if trend_slope > 0.5 else 'downward' if trend_slope < -0.5 else 'stable',
                        'slope': trend_slope,
                        'volatility': volatility,
                        'momentum': momentum,
                        'quality': trend_quality,
                        'data_points': len(recent_points)
                    }
        if recent_games:
            wins = sum(1 for g in recent_games if g.get('winner') == data['profile']['username'])
            losses = sum(1 for g in recent_games if g.get('winner') and g.get('winner') != data['profile']['username'])
            draws = sum(1 for g in recent_games if not g.get('winner'))
            total_games = len(recent_games)
            win_rate = wins / total_games if total_games > 0 else 0
            loss_rate = losses / total_games if total_games > 0 else 0
            draw_rate = draws / total_games if total_games > 0 else 0
            tc_performance = {}
            for game in recent_games:
                tc = game.get('perf', 'unknown')
                if tc not in tc_performance:
                    tc_performance[tc] = {'wins': 0, 'losses': 0, 'total': 0}
                tc_performance[tc]['total'] += 1
                if game.get('winner') == data['profile']['username']:
                    tc_performance[tc]['wins'] += 1
                elif game.get('winner'):
                    tc_performance[tc]['losses'] += 1
            opening_performance = {}
            for game in recent_games:
                opening = game.get('opening', {}).get('name')
                if opening:
                    if opening not in opening_performance:
                        opening_performance[opening] = {'wins': 0, 'losses': 0, 'total': 0, 'avg_opponent_rating': 0}
                    opening_performance[opening]['total'] += 1
                    opponent_rating = 0
                    if game.get('players', {}).get('white', {}).get('user', {}).get('name') == data['profile']['username']:
                        opponent_rating = game.get('players', {}).get('black', {}).get('rating', 0)
                    else:
                        opponent_rating = game.get('players', {}).get('white', {}).get('rating', 0)
                    opening_performance[opening]['avg_opponent_rating'] += opponent_rating
                    if game.get('winner') == data['profile']['username']:
                        opening_performance[opening]['wins'] += 1
                    elif game.get('winner'):
                        opening_performance[opening]['losses'] += 1
            for opening in opening_performance:
                if opening_performance[opening]['total'] > 0:
                    opening_performance[opening]['avg_opponent_rating'] /= opening_performance[opening]['total']
            white_games = [g for g in recent_games if g.get('players', {}).get('white', {}).get('user', {}).get('name') == data['profile']['username']]
            black_games = [g for g in recent_games if g.get('players', {}).get('black', {}).get('user', {}).get('name') == data['profile']['username']]
            white_wins = sum(1 for g in white_games if g.get('winner') == 'white')
            black_wins = sum(1 for g in black_games if g.get('winner') == 'black')
            white_win_rate = white_wins / len(white_games) if white_games else 0
            black_win_rate = black_wins / len(black_games) if black_games else 0
            ratings = [v.get('rating', 0) for v in data['stats'].values() if v.get('rating', 0) > 0 and v.get('games', 0) > 10]
            rating_gap = max(ratings) - min(ratings) if ratings else 0
            recent_ratings = []
            for cat in data['history']:
                if cat['points']:
                    recent_points = []
                    for point in cat['points']:
                        point_date = datetime(point[0], point[1] + 1, point[2])
                        if point_date >= six_months_ago:
                            recent_points.append(point)
                    if recent_points:
                        recent_ratings.extend([p[3] for p in recent_points])
            consistency_score = 0
            if recent_ratings:
                mean_rating = np.mean(recent_ratings)
                std_dev = np.std(recent_ratings)
                consistency_score = 1 - (std_dev / mean_rating) if mean_rating > 0 else 0
            performance_patterns = {
                'win_rate': win_rate,
                'loss_rate': loss_rate,
                'draw_rate': draw_rate,
                'total_games': total_games,
                'time_control_performance': tc_performance,
                'opening_performance': opening_performance,
                'white_win_rate': white_win_rate,
                'black_win_rate': black_win_rate,
                'rating_gap': rating_gap,
                'consistency_score': consistency_score
            }
        else:
            performance_patterns = {}
        valid_tcs = {k: v for k, v in data['stats'].items() if k != 'puzzle' and v.get('games', 0) > 10}
        if valid_tcs:
            best = max(valid_tcs, key=lambda k: valid_tcs[k].get('rating', 0))
            worst = min(valid_tcs, key=lambda k: valid_tcs[k].get('rating', 0))
        else:
            best = worst = None
        analytics = {
            "trends": trends,
            "performance_patterns": performance_patterns,
            "best": best,
            "worst": worst,
            "analysis_period": "Last 6 months",
            "total_analyzed_games": len(recent_games)
        }
        return analytics

class NarrativeAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Elite Chess Performance Coach",
            goal="Generate sophisticated, actionable chess insights that impress players and provide real improvement strategies. Do not include puzzles ratings in the insights.",
            backstory="Former Grandmaster turned performance coach with 20+ years of experience analyzing chess patterns, psychological aspects, and strategic development. Expert at translating complex analytics into motivating, actionable advice that transforms players."
        )
    
    def run(self, analytics, data):
        # This agent is now a pure data container; LLM prompt will be handled in the crew pipeline
        return {"analytics": analytics, "data": data}

class UIAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Dashboard UI Architect",
            goal="Transform processed data into dashboard-ready JSON schema for React frontend",
            backstory="Specialist in creating structured data schemas that power modern web dashboards",
            llm=llm
        )
    
    def run(self, data, analytics, insights):
        return {
            "overview": {
                "username": data['profile']['username'],
                "avatar": f"https://lichess.org/api/user/{data['profile']['username']}/avatar",
                "ratings": data['stats']
            },
            "ratingHistory": data['history'],
            "recentGames": data['games'],
            "insights": insights
        }

class ChatAgent:
    def __init__(self):
        # Use the same LLM as other agents
        from llm_config import get_llm
        self.llm = llm if llm is not None else get_llm("openai")

    async def run(self, username: str, message: str):
        import httpx
        base_url = "https://lichess.org/api"
        async with httpx.AsyncClient() as client:
            profile_resp = await client.get(f"{base_url}/user/{username}")
            stats_resp = await client.get(f"{base_url}/user/{username}")
            history_resp = await client.get(f"{base_url}/user/{username}/rating-history")

        if profile_resp.status_code != 200:
            return "Sorry, I couldn't find your profile."

        profile = profile_resp.json()
        stats = stats_resp.json().get("perfs", {})
        history = history_resp.json() if history_resp.status_code == 200 else []

        # Compose a system prompt for the LLM
        system_prompt = (
            f"You are a chess assistant. The user '{username}' asked: '{message}'. "
            f"Here is their chess profile: {json.dumps(profile)}. "
            f"Here are their stats: {json.dumps(stats)}. "
            f"Here is their rating history: {json.dumps(history)}. "
            "Answer the user's question using this data. If the question is about ranking, games, or skills, provide a helpful, specific answer. "
            "If the data is missing, say so. Be concise and friendly."
        )

        # Call the LLM to generate a response
        if self.llm is not None:
            try:
                # CrewAI LLM interface: llm.invoke(prompt) or llm(prompt)
                if hasattr(self.llm, "invoke"):
                    response = self.llm.invoke(system_prompt)
                else:
                    response = self.llm(system_prompt)
                return response
            except Exception as e:
                return f"[LLM error] {str(e)}"
        else:
            # Fallback: simple logic if LLM is not available
            if "ranking" in message.lower():
                blitz = stats.get("blitz", {}).get("rating", "N/A")
                return f"Your blitz rating is {blitz}."
            elif "games" in message.lower():
                return f"You have played {profile.get('count', {}).get('all', 'N/A')} games."
            elif "skills" in message.lower():
                return f"Your best performance is in {max(stats, key=lambda k: stats[k].get('rating', 0))}."
            else:
                return "Ask me about your ranking, games, or skills!"


# --- CREW PIPELINE ---

# --- CREW PIPELINE using CrewAI Crew ---
from crewai import Crew

def main(username):
    # Instantiate agents
    data_agent = DataAgent()
    analytics_agent = AnalyticsAgent()
    narrative_agent = NarrativeAgent()
    ui_agent = UIAgent()

    # Step 1: DataAgent fetches user data
    data = data_agent.run(username)

    # Step 2: AnalyticsAgent analyzes data
    analytics = analytics_agent.run(data)

    # Step 3: NarrativeAgent generates insights using kickoff()
    narrative_prompt = (
        f"As a {narrative_agent.role}, your goal is: {narrative_agent.goal}. "
        f"Here is the user's analytics data: {json.dumps(analytics)}. "
        f"Here is the user's raw data: {json.dumps(data)}. "
        "Generate sophisticated, actionable chess insights and improvement strategies for the user, in a JSON array of objects with fields: type, title, message, action. Do not include puzzle ratings. Include at least 10 insights on rating trends, time control strengths/weaknesses, opening performance, color performance, consistency, and psychological aspects. Make the insights motivating and impressive."
    )
    insights_result = narrative_agent.kickoff(narrative_prompt)
    try:
        insights = json.loads(insights_result.raw)
    except Exception:
        insights = [{"type": "info", "title": "LLM Output", "message": insights_result.raw, "action": ""}]

    # Step 4: UIAgent generates dashboard (optionally with LLM summary)
    dashboard = ui_agent.run(data, analytics, insights)
    ui_prompt = (
        f"As a {ui_agent.role}, your goal is: {ui_agent.goal}. "
        f"Here is the dashboard data: {json.dumps(dashboard)}. "
        "Write a short summary for the user to display at the top of their dashboard."
    )
    dashboard_summary = ui_agent.kickoff(ui_prompt)
    dashboard["llm_summary"] = dashboard_summary.raw

    print("\n=== Dashboard JSON ===\n")
    print(json.dumps(dashboard, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True)
    args = parser.parse_args()
    main(args.user) 