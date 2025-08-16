import sys
import argparse
import asyncio
import httpx
from crewai import Agent, Crew, Task

MCP_SERVER = "http://localhost:8000"

# --- AGENTS ---
class DataAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Data Retrieval Specialist",
            goal="Fetch comprehensive user data from Lichess via MCP server",
            backstory="Expert at gathering chess player statistics, ratings, and game history from Lichess API"
        )
    
    def run(self, username):
        # Note: CrewAI agents don't support async by default, so we'll use sync
        with httpx.Client() as client:
            profile = client.get(f"{MCP_SERVER}/user/{username}/profile").json()
            stats = client.get(f"{MCP_SERVER}/user/{username}/stats").json()
            history = client.get(f"{MCP_SERVER}/user/{username}/history").json()
            games = client.get(f"{MCP_SERVER}/user/{username}/games").json()
        return {"profile": profile, "stats": stats, "history": history, "games": games}

class AnalyticsAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chess Analytics Expert",
            goal="Analyze rating trends, win/loss ratios, and identify strong/weak time controls",
            backstory="Specialist in chess performance analysis with expertise in statistical trends and pattern recognition"
        )
    
    def run(self, data):
        # Analyze rating trends, win/loss, strong/weak time controls
        import numpy as np
        trends = {}
        for cat in data['history']:
            points = [p[3] for p in cat['points']] if cat['points'] else []
            if len(points) > 2:
                trend = np.polyfit(range(len(points)), points, 1)[0]
                if trend > 0.5:
                    trends[cat['name']] = 'upward'
                elif trend < -0.5:
                    trends[cat['name']] = 'downward'
                else:
                    trends[cat['name']] = 'stable'
        # Win/loss ratio (recent games)
        wins = sum(1 for g in data['games'] if g.get('winner') == data['profile']['username'])
        losses = sum(1 for g in data['games'] if g.get('winner') and g.get('winner') != data['profile']['username'])
        ratios = {"win": wins, "loss": losses}
        # Strong/weak time controls
        best = max(data['stats'], key=lambda k: data['stats'][k].get('rating', 0))
        worst = min(data['stats'], key=lambda k: data['stats'][k].get('rating', 0))
        return {"trends": trends, "ratios": ratios, "best": best, "worst": worst}

class NarrativeAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Chess Performance Narrator",
            goal="Generate human-readable insights and motivational summaries from chess analytics",
            backstory="Expert at translating complex chess statistics into clear, actionable insights for players"
        )
    
    def run(self, analytics, data):
        # Generate insights
        insights = []
        for cat, trend in analytics['trends'].items():
            if trend == 'upward':
                insights.append(f"Your {cat} rating is trending upward in the last 30 days.")
            elif trend == 'downward':
                insights.append(f"Your {cat} rating is trending downward recently.")
            else:
                insights.append(f"Your {cat} rating is stable.")
        insights.append(f"Win/Loss ratio: {analytics['ratios']['win']} / {analytics['ratios']['loss']}")
        insights.append(f"Your strongest time control: {analytics['best']}")
        insights.append(f"Your weakest time control: {analytics['worst']}")
        return insights

class UIAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Dashboard UI Architect",
            goal="Transform processed data into dashboard-ready JSON schema for React frontend",
            backstory="Specialist in creating structured data schemas that power modern web dashboards"
        )
    
    def run(self, data, analytics, insights):
        # Output dashboard schema
        return {
            "overview": {
                "username": data['profile']['username'],
                "avatar": f"https://lichess.org/api/user/{data['profile']['username']}/avatar",
                "ratings": {k: v.get('rating') for k, v in data['stats'].items()}
            },
            "ratingHistory": data['history'],
            "recentGames": data['games'],
            "insights": insights
        }

# --- CREW PIPELINE ---
def main(username):
    data_agent = DataAgent()
    analytics_agent = AnalyticsAgent()
    narrative_agent = NarrativeAgent()
    ui_agent = UIAgent()

    data = data_agent.run(username)
    analytics = analytics_agent.run(data)
    insights = narrative_agent.run(analytics, data)
    dashboard = ui_agent.run(data, analytics, insights)
    print("\n=== Dashboard JSON ===\n")
    import json
    print(json.dumps(dashboard, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True)
    args = parser.parse_args()
    main(args.user) 