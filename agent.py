import os
from crewai import Agent, Task, Crew
from openai import OpenAI
from lichess_tools import get_lichess_perfs, get_lichess_rating_history
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Create an agent
lichess_agent = Agent(
    role="Expert Chess Coach",
    backstory="Provides insights and advice on chess strategies based on Lichess player data.",
    goal="Provide expert advice and insights on chess strategies and player performance based on Lichess data for given player id by getting performance stats and rating history.",
    tools=[get_lichess_perfs, get_lichess_rating_history],
    verbose=True
)

# Use kickoff() to interact directly with the agent
result = lichess_agent.kickoff('slowbluesman')

# Access the raw response
print(result.raw)
