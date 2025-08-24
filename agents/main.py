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
        # Advanced chess analytics using only last 6 months of data
        import numpy as np
        from datetime import datetime, timedelta
        
        # Calculate 6 months ago timestamp
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Filter data to last 6 months only
        recent_games = []
        for game in data['games']:
            game_timestamp = game.get('createdAt', 0) / 1000  # Convert from milliseconds
            game_date = datetime.fromtimestamp(game_timestamp)
            if game_date >= six_months_ago:
                recent_games.append(game)
        
        # Recent rating trends (last 6 months)
        trends = {}
        for cat in data['history']:
            if cat['points']:
                # Filter to last 6 months
                recent_points = []
                for point in cat['points']:
                    point_date = datetime(point[0], point[1] + 1, point[2])  # Month is 0-indexed
                    if point_date >= six_months_ago:
                        recent_points.append(point)
                
                if len(recent_points) >= 3:
                    # Calculate trend with more sophisticated analysis
                    ratings = [p[3] for p in recent_points]
                    dates = [i for i in range(len(recent_points))]
                    
                    # Linear regression for trend
                    trend_slope = np.polyfit(dates, ratings, 1)[0]
                    
                    # Calculate volatility (standard deviation)
                    volatility = np.std(ratings)
                    
                    # Calculate momentum (rate of change acceleration)
                    if len(ratings) >= 4:
                        momentum = np.polyfit(dates, ratings, 2)[0] * 2  # Second derivative
                    else:
                        momentum = 0
                    
                    # Determine trend quality
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
        
        # Advanced win/loss analysis with psychological patterns
        if recent_games:
            wins = sum(1 for g in recent_games if g.get('winner') == data['profile']['username'])
            losses = sum(1 for g in recent_games if g.get('winner') and g.get('winner') != data['profile']['username'])
            draws = sum(1 for g in recent_games if not g.get('winner'))
            total_games = len(recent_games)
            
            win_rate = wins / total_games if total_games > 0 else 0
            loss_rate = losses / total_games if total_games > 0 else 0
            draw_rate = draws / total_games if total_games > 0 else 0
            
            # Analyze performance patterns
            performance_patterns = {}
            
            # Time control performance
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
            
            # Opening performance analysis
            opening_performance = {}
            for game in recent_games:
                opening = game.get('opening', {}).get('name')
                if opening:
                    if opening not in opening_performance:
                        opening_performance[opening] = {'wins': 0, 'losses': 0, 'total': 0, 'avg_opponent_rating': 0}
                    
                    opening_performance[opening]['total'] += 1
                    opponent_rating = 0
                    
                    # Get opponent rating
                    if game.get('players', {}).get('white', {}).get('user', {}).get('name') == data['profile']['username']:
                        opponent_rating = game.get('players', {}).get('black', {}).get('rating', 0)
                    else:
                        opponent_rating = game.get('players', {}).get('white', {}).get('rating', 0)
                    
                    opening_performance[opening]['avg_opponent_rating'] += opponent_rating
                    
                    if game.get('winner') == data['profile']['username']:
                        opening_performance[opening]['wins'] += 1
                    elif game.get('winner'):
                        opening_performance[opening]['losses'] += 1
            
            # Calculate average opponent ratings
            for opening in opening_performance:
                if opening_performance[opening]['total'] > 0:
                    opening_performance[opening]['avg_opponent_rating'] /= opening_performance[opening]['total']
            
            # Psychological pattern analysis
            white_games = [g for g in recent_games if g.get('players', {}).get('white', {}).get('user', {}).get('name') == data['profile']['username']]
            black_games = [g for g in recent_games if g.get('players', {}).get('black', {}).get('user', {}).get('name') == data['profile']['username']]
            
            white_wins = sum(1 for g in white_games if g.get('winner') == 'white')
            black_wins = sum(1 for g in black_games if g.get('winner') == 'black')
            
            white_win_rate = white_wins / len(white_games) if white_games else 0
            black_win_rate = black_wins / len(black_games) if black_games else 0
            
            # Rating gap analysis
            ratings = [v.get('rating', 0) for v in data['stats'].values() if v.get('rating', 0) > 0 and v.get('games', 0) > 10]
            rating_gap = max(ratings) - min(ratings) if ratings else 0
            
            # Consistency analysis using recent data
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
        
        # Strong/weak time controls (excluding puzzles)
        valid_tcs = {k: v for k, v in data['stats'].items() if k != 'puzzle' and v.get('games', 0) > 10}
        if valid_tcs:
            best = max(valid_tcs, key=lambda k: valid_tcs[k].get('rating', 0))
            worst = min(valid_tcs, key=lambda k: valid_tcs[k].get('rating', 0))
        else:
            best = worst = None
        
        return {
            "trends": trends,
            "performance_patterns": performance_patterns,
            "best": best,
            "worst": worst,
            "analysis_period": "Last 6 months",
            "total_analyzed_games": len(recent_games)
        }

class NarrativeAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Elite Chess Performance Coach",
            goal="Generate sophisticated, actionable chess insights that impress players and provide real improvement strategies. Do not include puzzles ratings in the insights.",
            backstory="Former Grandmaster turned performance coach with 20+ years of experience analyzing chess patterns, psychological aspects, and strategic development. Expert at translating complex analytics into motivating, actionable advice that transforms players."
        )
    
    def run(self, analytics, data):
        # Generate world-class, expert-level chess coaching insights
        insights = []
        
        # Analysis period context
        analysis_period = analytics.get('analysis_period', 'Last 6 months')
        total_games = analytics.get('total_analyzed_games', 0)
        
        if total_games == 0:
            insights.append({
                "type": "info",
                "title": "📊 Data Analysis Period",
                "message": f"No recent games found in the {analysis_period.lower()}. This could indicate a break from chess or limited recent activity.",
                "action": "Consider playing more games to get personalized insights, or extend the analysis period to see longer-term patterns."
            })
            return insights
        
        # Rating trend analysis with expert coaching perspective
        for cat, trend_data in analytics.get('trends', {}).items():
            if cat == 'Puzzles':  # Skip puzzles as requested
                continue
                
            direction = trend_data.get('direction')
            slope = trend_data.get('slope', 0)
            volatility = trend_data.get('volatility', 0)
            momentum = trend_data.get('momentum', 0)
            quality = trend_data.get('quality')
            data_points = trend_data.get('data_points', 0)
            
            if direction == 'upward':
                if quality == 'strong':
                    insights.append({
                        "type": "success",
                        "title": f"🚀 {cat} Rating Breakthrough",
                        "message": f"Exceptional {cat} performance! Your rating is climbing at {abs(slope):.1f} points per period with low volatility ({volatility:.1f}). This indicates mastery of {cat}-specific time management and decision-making patterns.",
                        "action": f"Leverage this momentum by studying {cat} endgames and practicing against higher-rated opponents. Your current trajectory suggests you're ready for the next level."
                    })
                else:
                    insights.append({
                        "type": "success",
                        "title": f"📈 {cat} Rating Momentum",
                        "message": f"Solid {cat} improvement with {abs(slope):.1f} points per period. While there's some volatility ({volatility:.1f}), this shows you're adapting to {cat} dynamics.",
                        "action": f"Focus on reducing volatility by developing consistent opening preparation and time management routines specific to {cat} chess."
                    })
            elif direction == 'downward':
                if quality == 'strong':
                    insights.append({
                        "type": "warning",
                        "title": f"📉 {cat} Rating Challenge",
                        "message": f"Significant {cat} decline of {abs(slope):.1f} points per period with low volatility ({volatility:.1f}). This suggests a systematic issue rather than random variance.",
                        "action": f"Take a strategic break from {cat}, analyze your recent losses for patterns, and return with a refreshed opening repertoire. Consider working with a coach on {cat}-specific weaknesses."
                    })
                else:
                    insights.append({
                        "type": "warning",
                        "title": f"⚖️ {cat} Rating Adjustment",
                        "message": f"Moderate {cat} decline of {abs(slope):.1f} points with high volatility ({volatility:.1f}). This suggests inconsistent preparation or psychological factors affecting performance.",
                        "action": f"Develop a consistent pre-game routine and focus on opening preparation. The volatility suggests you have the skills but need to stabilize your mental game."
                    })
            else:  # stable
                if volatility < 30:
                    insights.append({
                        "type": "info",
                        "title": f"🎯 {cat} Rating Plateau",
                        "message": f"Your {cat} rating is remarkably stable with very low volatility ({volatility:.1f}). This indicates consistent performance but suggests you've hit a skill ceiling.",
                        "action": f"Break through this plateau by studying advanced {cat} strategies, analyzing master games, and challenging yourself against higher-rated opponents."
                    })
                else:
                    insights.append({
                        "type": "info",
                        "title": f"⚖️ {cat} Rating Stability",
                        "message": f"Your {cat} rating is holding steady despite some volatility ({volatility:.1f}). This suggests you're maintaining your level while adapting to different playing styles.",
                        "action": f"Use this stability to build confidence and gradually increase the difficulty of your opponents. Focus on converting draws to wins in advantageous positions."
                    })
        
        # Performance pattern analysis with psychological insights
        performance = analytics.get('performance_patterns', {})
        if performance:
            win_rate = performance.get('win_rate', 0)
            loss_rate = performance.get('loss_rate', 0)
            draw_rate = performance.get('draw_rate', 0)
            total_games = performance.get('total_games', 0)
            
            # Win rate analysis with expert perspective
            if win_rate > 0.65:
                insights.append({
                    "type": "success",
                    "title": "🏆 Elite Performance Level",
                    "message": f"Outstanding {win_rate:.1%} win rate over {total_games} games! This performance level suggests you're significantly underrated or have made a major breakthrough in your chess understanding.",
                    "action": "Leverage this exceptional form by playing in tournaments and challenging much higher-rated opponents. Your current level suggests you're ready for serious competitive chess."
                })
            elif win_rate > 0.55:
                insights.append({
                    "type": "success",
                    "title": "📈 Strong Competitive Performance",
                    "message": f"Solid {win_rate:.1%} win rate shows you're competing well above your rating level. This indicates strong preparation and psychological resilience.",
                    "action": "Continue this momentum by maintaining your current study routine and gradually increasing opponent difficulty. You're on track for significant rating improvement."
                })
            elif win_rate < 0.35:
                insights.append({
                    "type": "warning",
                    "title": "💪 Growth Through Challenge",
                    "message": f"Current {win_rate:.1%} win rate indicates you're facing strong opposition. This is actually excellent for development - you're playing opponents who push your limits and expose weaknesses.",
                    "action": "Embrace these challenges as learning opportunities. After each loss, identify one specific mistake and practice that scenario. Your rating will catch up to your improved play."
                })
            else:  # 0.35 - 0.55
                insights.append({
                    "type": "info",
                    "title": "⚖️ Balanced Competitive Level",
                    "message": f"Win rate of {win_rate:.1%} shows you're competing at your current rating level. This balanced performance is perfect for steady, sustainable improvement.",
                    "action": "Maintain this balance while gradually increasing difficulty. Focus on converting draws to wins and developing endgame technique to push your win rate higher."
                })
            
            # Draw rate analysis with strategic insights
            if draw_rate > 0.25:
                insights.append({
                    "type": "strategy",
                    "title": "🤝 Defensive Mastery",
                    "message": f"High draw rate of {draw_rate:.1%} indicates excellent defensive skills and the ability to hold your own against strong opponents. This is crucial for tournament success.",
                    "action": "Study endgame technique to convert some draws to wins. Focus on king and pawn endgames, which often decide close games. Your defensive foundation is excellent."
                })
            
            # Time control performance analysis
            tc_performance = performance.get('time_control_performance', {})
            if tc_performance:
                # Find best and worst performing time controls
                tc_win_rates = {}
                for tc, stats in tc_performance.items():
                    if stats['total'] >= 3:  # Minimum games for meaningful analysis
                        tc_win_rates[tc] = stats['wins'] / stats['total']
                
                if tc_win_rates:
                    best_tc = max(tc_win_rates.items(), key=lambda x: x[1])
                    worst_tc = min(tc_win_rates.items(), key=lambda x: x[1])
                    
                    if best_tc[1] > 0.6:
                        insights.append({
                            "type": "strategy",
                            "title": f"🎯 {best_tc[0].title()} Mastery",
                            "message": f"Exceptional {best_tc[0]} performance with {best_tc[1]:.1%} win rate! This time control clearly suits your playing style and preparation level.",
                            "action": f"Use your {best_tc[0]} strength to build confidence and tournament success. Study {best_tc[0]}-specific strategies and consider specializing in this format."
                        })
                    
                    if worst_tc[1] < 0.4 and tc_performance[worst_tc[0]]['total'] >= 5:
                        insights.append({
                            "type": "strategy",
                            "title": f"🔧 {worst_tc[0].title()} Development",
                            "message": f"Your {worst_tc[0]} performance needs attention with only {worst_tc[1]:.1%} wins. This suggests either poor preparation or a fundamental mismatch with your playing style.",
                            "action": f"Either invest serious time studying {worst_tc[0]} openings and endgames, or consider replacing it with something that better fits your strengths. Don't force a square peg into a round hole."
                        })
            
            # Opening performance analysis with deep insights
            opening_performance = performance.get('opening_performance', {})
            if opening_performance:
                # Analyze openings by success rate and opponent strength
                opening_analysis = []
                for opening, stats in opening_performance.items():
                    if stats['total'] >= 3:  # Minimum games for analysis
                        win_rate = stats['wins'] / stats['total']
                        avg_opponent = stats['avg_opponent_rating']
                        opening_analysis.append({
                            'name': opening,
                            'win_rate': win_rate,
                            'avg_opponent': avg_opponent,
                            'total': stats['total']
                        })
                
                if opening_analysis:
                    # Sort by win rate
                    opening_analysis.sort(key=lambda x: x['win_rate'], reverse=True)
                    
                    best_opening = opening_analysis[0]
                    if best_opening['win_rate'] > 0.7:
                        insights.append({
                            "type": "opening",
                            "title": f"♟️ {best_opening['name']} - Your Weapon",
                            "message": f"'{best_opening['name']}' is your secret weapon with {best_opening['win_rate']:.1%} wins against opponents averaging {best_opening['avg_opponent']:.0f} rating! This opening clearly suits your style.",
                            "action": f"Deepen your knowledge of '{best_opening['name']}' by studying master games, learning 6-8 variations, and practicing against different responses. This could become your signature opening."
                        })
                    
                    # Analyze worst performing opening
                    worst_opening = opening_analysis[-1]
                    if worst_opening['win_rate'] < 0.3 and worst_opening['total'] >= 5:
                        insights.append({
                            "type": "opening",
                            "title": f"🔧 {worst_opening['name']} - Strategic Decision",
                            "message": f"'{worst_opening['name']}' is giving you trouble with only {worst_opening['win_rate']:.1%} wins. This suggests either poor preparation or a fundamental mismatch with your playing style.",
                            "action": f"Make a strategic decision: either invest serious time mastering '{worst_opening['name']}' or replace it with something that better fits your strengths. Life's too short for bad openings."
                        })
            
            # Psychological pattern analysis
            white_win_rate = performance.get('white_win_rate', 0)
            black_win_rate = performance.get('black_win_rate', 0)
            
            if abs(white_win_rate - black_win_rate) > 0.15:  # Significant difference
                if white_win_rate > black_win_rate:
                    insights.append({
                        "type": "psychology",
                        "title": "⚪ Initiative Player Profile",
                        "message": f"You perform significantly better as White ({white_win_rate:.1%} vs {black_win_rate:.1%} as Black). This suggests you excel at dictating the game's direction and may struggle with reactive play.",
                        "action": "Develop your Black repertoire by studying counter-attacking openings like the Sicilian Defense or King's Indian. Your White strength indicates you have the skills - now develop the Black side."
                    })
                else:
                    insights.append({
                        "type": "psychology",
                        "title": "⚫ Counter-Attack Specialist",
                        "message": f"You excel as Black ({black_win_rate:.1%} vs {white_win_rate:.1%} as White)! This indicates exceptional defensive skills and the ability to counter-attack effectively - rare and valuable traits.",
                        "action": "Leverage your Black strength by studying counter-attacking openings. Develop your White play by studying initiative-taking strategies. You're naturally gifted at reactive chess."
                    })
            
            # Rating gap analysis with development insights
            rating_gap = performance.get('rating_gap', 0)
            if rating_gap > 400:
                insights.append({
                    "type": "development",
                    "title": "🎭 Specialization vs. Versatility",
                    "message": f"Your rating gap of {rating_gap} points between formats suggests you're a specialist rather than a generalist. While specialization can work, consistency across formats builds overall chess strength.",
                    "action": "Identify why you excel in your strongest format and apply those principles to your weakest format. Consider whether you want to be a specialist or develop versatility - both are valid paths."
                })
            
            # Consistency analysis with mental game insights
            consistency_score = performance.get('consistency_score', 0)
            if consistency_score > 0.85:
                insights.append({
                    "type": "success",
                    "title": "🎯 Mental Discipline Master",
                    "message": f"Exceptional consistency score of {consistency_score:.1%}! This indicates strong mental discipline, consistent preparation, and psychological resilience. Players with high consistency often perform better under pressure.",
                    "action": "Leverage your consistency by playing in tournaments where steady performance is rewarded. Your mental game is a major strength - use it to your advantage in competitive play."
                })
            elif consistency_score < 0.7:
                insights.append({
                    "type": "warning",
                    "title": "📈 Consistency Development",
                    "message": f"Consistency score of {consistency_score:.1%} indicates some volatility. While this can indicate aggressive play, it also suggests room for improvement in preparation and mental game.",
                    "action": "Develop a consistent pre-game routine, focus on opening preparation, and work on emotional control during games. Consistency is a skill that can be developed."
                })
        
        # Add analysis period context
        insights.append({
            "type": "info",
            "title": "📊 Analysis Period Context",
            "message": f"All insights are based on your performance over the {analysis_period.lower()} ({total_games} games analyzed). This focused timeframe ensures relevance to your current form and recent improvements.",
            "action": "Use these insights to guide your next 6 months of training. Revisit this analysis regularly to track your progress and adjust your training plan."
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