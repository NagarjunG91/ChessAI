import argparse
import subprocess
import sys
import os

parser = argparse.ArgumentParser(description='Run MCP server and CrewAI agents.')
parser.add_argument('--user', type=str, required=True, help='Lichess username')
args = parser.parse_args()

# Get the virtual environment Python path
venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
if not os.path.exists(venv_python):
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'python.exe')  # Windows

# Start MCP server (in background)
server_proc = subprocess.Popen([venv_python, '-m', 'uvicorn', 'server.main:app', '--reload'])

try:
    # Run CrewAI agents pipeline
    subprocess.run([venv_python, 'agents/main.py', '--user', args.user], check=True)
finally:
    server_proc.terminate() 