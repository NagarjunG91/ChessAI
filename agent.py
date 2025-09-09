import os
from crewai import LLM, Agent, Task, Crew
from openai import OpenAI
from lichess_tools import get_lichess_perfs, get_lichess_rating_history, get_lichess_performance
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = LLM(
            model="azure/gpt-4.1-mini",
            api_key=os.getenv("AZURE_API_KEY")
        )

# Create an agent
lichess_agent = Agent(
    role="Expert Chess Coach",
    backstory="Chess player with 30 years of experience in the game and a master of chess strategies with 10 years of experience in coaching.",
    goal="Provide detailed expert advice to improve the player's chess strategies and player performance based on Lichess data for given player id by getting performance stats and rating history only for blitz format.",
    tools=[get_lichess_rating_history, get_lichess_performance],
    verbose=True,
    llm=llm
)

# Use kickoff() to interact directly with the agent
result = lichess_agent.kickoff('slowbluesman')

# Access the raw response
print(result.raw)