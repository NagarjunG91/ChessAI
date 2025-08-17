import sys
import argparse
import asyncio
import httpx
import os
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
            backstory="Specialist in chess performance analysis with expertise in statistical trends and pattern recognition",
            llm=llm
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
        draws = sum(1 for g in data['games'] if not g.get('winner'))
        ratios = {"win": wins, "loss": losses, "draw": draws}
        
        # Strong/weak time controls
        best = max(data['stats'], key=lambda k: data['stats'][k].get('rating', 0))
        worst = min(data['stats'], key=lambda k: data['stats'][k].get('rating', 0))
        
        # Advanced analytics
        # Opening success analysis
        opening_stats = {}
        for game in data['games']:
            opening = game.get('opening', {}).get('name')
            if opening:
                if opening not in opening_stats:
                    opening_stats[opening] = {'wins': 0, 'losses': 0, 'total': 0}
                
                opening_stats[opening]['total'] += 1
                if game.get('winner') == data['profile']['username']:
                    opening_stats[opening]['wins'] += 1
                elif game.get('winner'):
                    opening_stats[opening]['losses'] += 1
        
        # Performance consistency analysis
        recent_ratings = []
        for cat in data['history']:
            if cat['points'] and len(cat['points']) >= 3:
                recent_points = cat['points'][-3:]  # Last 3 data points
                recent_ratings.extend([p[3] for p in recent_points])
        
        consistency_score = 0
        if recent_ratings:
            # Calculate standard deviation to measure consistency
            mean_rating = np.mean(recent_ratings)
            std_dev = np.std(recent_ratings)
            consistency_score = 1 - (std_dev / mean_rating) if mean_rating > 0 else 0
        
        # Psychological pattern analysis
        psychological_patterns = []
        if len(data['games']) >= 5:
            # Analyze if player performs better as white or black
            white_games = [g for g in data['games'] if g.get('players', {}).get('white', {}).get('user', {}).get('name') == data['profile']['username']]
            black_games = [g for g in data['games'] if g.get('players', {}).get('black', {}).get('user', {}).get('name') == data['profile']['username']]
            
            white_wins = sum(1 for g in white_games if g.get('winner') == 'white')
            black_wins = sum(1 for g in black_games if g.get('winner') == 'black')
            
            white_win_rate = white_wins / len(white_games) if white_games else 0
            black_win_rate = black_wins / len(black_games) if black_games else 0
            
            if abs(white_win_rate - black_win_rate) > 0.2:
                if white_win_rate > black_win_rate:
                    psychological_patterns.append("white_preference")
                else:
                    psychological_patterns.append("black_preference")
        
        return {
            "trends": trends, 
            "ratios": ratios, 
            "best": best, 
            "worst": worst,
            "opening_stats": opening_stats,
            "consistency_score": consistency_score,
            "psychological_patterns": psychological_patterns
        }

class NarrativeAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Elite Chess Performance Coach",
            goal="Generate sophisticated, actionable chess insights that impress players and provide real improvement strategies",
            backstory="Former Grandmaster turned performance coach with 20+ years of experience analyzing chess patterns, psychological aspects, and strategic development. Expert at translating complex analytics into motivating, actionable advice that transforms players."
        )
    
    def run(self, analytics, data):
        # Generate sophisticated, coach-like insights
        insights = []
        
        # Analyze rating trends with coaching perspective
        for cat, trend in analytics['trends'].items():
            if trend == 'upward':
                insights.append({
                    "type": "success",
                    "title": f"🚀 {cat} Rating Momentum",
                    "message": f"Your {cat} rating is climbing steadily! This suggests you're mastering the time pressure and decision-making patterns specific to {cat} chess. Keep this momentum by focusing on opening preparation and endgame technique.",
                    "action": f"Practice {cat} endgames and study common {cat} openings to maintain this upward trajectory."
                })
            elif trend == 'downward':
                insights.append({
                    "type": "warning",
                    "title": f"📉 {cat} Rating Challenge",
                    "message": f"Your {cat} rating has been declining. This often indicates either psychological pressure or gaps in {cat}-specific strategy. Don't panic - this is a learning opportunity.",
                    "action": f"Take a break from {cat} for a few days, then return with fresh opening preparation and focus on time management."
                })
            else:
                insights.append({
                    "type": "info",
                    "title": f"⚖️ {cat} Rating Stability",
                    "message": f"Your {cat} rating is holding steady. While stability is good, consider this a plateau that you can break through with targeted improvement.",
                    "action": f"Identify your weakest {cat} openings and dedicate 30 minutes daily to studying them."
                })
        
        # Win/Loss analysis with psychological insights
        win_ratio = analytics['ratios']['win'] / (analytics['ratios']['win'] + analytics['ratios']['loss']) if (analytics['ratios']['win'] + analytics['ratios']['loss']) > 0 else 0
        
        if win_ratio > 0.6:
            insights.append({
                "type": "success",
                "title": "🏆 Winning Streak Analysis",
                "message": f"Impressive win rate of {win_ratio:.1%}! You're clearly in excellent form. This suggests strong opening preparation and psychological resilience.",
                "action": "Leverage this confidence by playing slightly higher-rated opponents to push your limits."
            })
        elif win_ratio < 0.4:
            insights.append({
                "type": "warning",
                "title": "💪 Building Resilience",
                "message": f"Current win rate of {win_ratio:.1%} indicates you're facing challenges. This is actually excellent for growth - you're playing opponents who push you to improve.",
                "action": "Focus on learning from losses. After each game, identify one specific mistake and practice that scenario."
            })
        else:
            insights.append({
                "type": "info",
                "title": "⚖️ Balanced Performance",
                "message": f"Win rate of {win_ratio:.1%} shows balanced play. You're competing well at your current level, which is perfect for steady improvement.",
                "action": "Maintain this balance while gradually increasing the difficulty of your opponents."
            })
        
        # Time control analysis with strategic advice
        best_tc = analytics['best']
        worst_tc = analytics['worst']
        
        insights.append({
            "type": "strategy",
            "title": f"🎯 Time Control Mastery",
            "message": f"Your strongest format is {best_tc} (rating: {data['stats'][best_tc]['rating']}), while {worst_tc} needs attention. This suggests you excel at quick tactical decisions but may struggle with deep strategic planning.",
            "action": f"Use your {best_tc} strength to build confidence, then transfer those tactical skills to {worst_tc} by practicing longer time controls."
        })
        
        # Recent performance analysis
        recent_games = data['games'][:5] if data['games'] else []
        if recent_games:
            recent_wins = sum(1 for g in recent_games if g.get('winner') == data['profile']['username'])
            recent_performance = "excellent" if recent_wins >= 4 else "good" if recent_wins >= 2 else "challenging"
            
            insights.append({
                "type": "performance",
                "title": "📊 Recent Form Analysis",
                "message": f"Your last 5 games show {recent_performance} form. Recent performance is crucial for confidence and momentum building.",
                "action": "Review your last 3 games to identify patterns in your wins and losses. Focus on replicating successful strategies."
            })
        
        # Opening analysis
        openings = [g.get('opening', {}).get('name') for g in data['games'] if g.get('opening', {}).get('name')]
        if openings:
            common_openings = {}
            for opening in openings:
                common_openings[opening] = common_openings.get(opening, 0) + 1
            
            most_played = max(common_openings.items(), key=lambda x: x[1])
            insights.append({
                "type": "opening",
                "title": "♟️ Opening Strategy Insight",
                "message": f"Your most played opening is '{most_played[0]}' ({most_played[1]} times). This shows you have a comfort zone, which is good for consistency.",
                "action": "Deepen your knowledge of this opening by studying master games and learning 3-4 variations to handle different responses."
            })
        
        # Rating gap analysis
        ratings = [v.get('rating', 0) for v in data['stats'].values() if v.get('rating', 0) > 0]
        if ratings:
            rating_gap = max(ratings) - min(ratings)
            if rating_gap > 500:
                insights.append({
                    "type": "development",
                    "title": "🎭 Multi-Format Challenge",
                    "message": f"Your rating gap between formats is {rating_gap} points. This suggests you're a specialist rather than a generalist - both approaches can work, but consistency across formats builds overall chess strength.",
                    "action": "Identify why you excel in your strongest format and apply those principles to your weakest format."
                })
        
        # Consistency analysis
        if analytics.get('consistency_score', 0) > 0.8:
            insights.append({
                "type": "success",
                "title": "🎯 Consistency Master",
                "message": "Your rating consistency is exceptional! This indicates strong mental discipline and consistent preparation. Players with high consistency often perform better under pressure.",
                "action": "Leverage your consistency by playing in tournaments where steady performance is rewarded."
            })
        elif analytics.get('consistency_score', 0) < 0.6:
            insights.append({
                "type": "warning",
                "title": "📈 Consistency Opportunity",
                "message": "Your rating shows some volatility. While this can indicate aggressive play, it also suggests room for improvement in preparation and mental game.",
                "action": "Focus on consistent opening preparation and develop a pre-game routine to stabilize performance."
            })
        
        # Opening analysis with success rates
        if analytics.get('opening_stats'):
            best_opening = max(analytics['opening_stats'].items(), key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0)
            worst_opening = min(analytics['opening_stats'].items(), key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0)
            
            best_win_rate = best_opening[1]['wins'] / best_opening[1]['total'] if best_opening[1]['total'] > 0 else 0
            worst_win_rate = worst_opening[1]['wins'] / worst_opening[1]['total'] if worst_opening[1]['total'] > 0 else 0
            
            if best_win_rate > 0.7:
                insights.append({
                    "type": "opening",
                    "title": "♟️ Opening Mastery",
                    "message": f"'{best_opening[0]}' is your weapon of choice with a {best_win_rate:.1%} win rate! This opening clearly suits your playing style and preparation level.",
                    "action": "Deepen your knowledge of this opening by studying master games and learning 5-6 variations to handle any response."
                })
            
            if worst_win_rate < 0.3 and worst_opening[1]['total'] >= 3:
                insights.append({
                    "type": "opening",
                    "title": "🔧 Opening Weakness",
                    "message": f"'{worst_opening[0]}' is giving you trouble with only {worst_win_rate:.1%} wins. This suggests either poor preparation or a mismatch with your playing style.",
                    "action": "Either invest serious time studying this opening or consider replacing it with something that better fits your strengths."
                })
        
        # Psychological pattern insights
        if analytics.get('psychological_patterns'):
            if 'white_preference' in analytics['psychological_patterns']:
                insights.append({
                    "type": "psychology",
                    "title": "⚪ White Side Advantage",
                    "message": "You perform significantly better as White. This suggests you prefer dictating the game's direction and may struggle with reactive play.",
                    "action": "Practice Black openings more frequently to develop your reactive skills and become a more versatile player."
                })
            elif 'black_preference' in analytics['psychological_patterns']:
                insights.append({
                    "type": "psychology",
                    "title": "⚫ Black Side Mastery",
                    "message": "You excel as Black! This indicates strong defensive skills and the ability to counter-attack effectively - valuable traits for any player.",
                    "action": "Leverage your Black strength by studying counter-attacking openings and developing your initiative-taking skills as White."
                })
        
        # Draw analysis
        if analytics['ratios'].get('draw', 0) > 0:
            draw_rate = analytics['ratios']['draw'] / (analytics['ratios']['win'] + analytics['ratios']['loss'] + analytics['ratios']['draw'])
            if draw_rate > 0.3:
                insights.append({
                    "type": "strategy",
                    "title": "🤝 Draw Specialist",
                    "message": f"With a {draw_rate:.1%} draw rate, you're excellent at holding your own against strong opponents. This defensive skill is crucial for tournament success.",
                    "action": "Study endgame technique to convert some of these draws into wins, especially in winning positions."
                })
        
        return insights

class UIAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Dashboard UI Architect",
            goal="Transform processed data into dashboard-ready JSON schema for React frontend",
            backstory="Specialist in creating structured data schemas that power modern web dashboards",
            llm=llm
        )
    
    def run(self, data, analytics, insights):
        # Output dashboard schema
        return {
            "overview": {
                "username": data['profile']['username'],
                "avatar": f"https://lichess.org/api/user/{data['profile']['username']}/avatar",
                "ratings": data['stats']  # Use the full stats object instead of extracting just rating
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
    print(json.dumps(dashboard, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True)
    args = parser.parse_args()
    main(args.user) 