from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.discord import DiscordTools
from agno.tools.email import EmailTools
agent_storage: str = "tmp/agents.db"
# llama_local_model.py
import requests
from typing import List
from agno.models.base import Model
from types import SimpleNamespace
import aiohttp
import asyncio

web_agent = Agent(
    name="Web Agent",
    model=Ollama(id="llama3.2"), #model=LLaMALocal(model="llama3"),
    tools=[GoogleSearchTools()],
    instructions=["Always include sources, always have a language input for the tool call"],
    # Store the agent sessions in a sqlite database
    storage=SqliteStorage(table_name="web_agent", db_file=agent_storage),
    # Adds the current date and time to the instructions
    add_datetime_to_instructions=True,
    # Adds the history of the conversation to the messages
    add_history_to_messages=True,
    # Number of history responses to add to the messages
    num_history_responses=5,
    # Adds markdown formatting to the messages
    markdown=True,
)

discord_agent = Agent(
    name="Discord Messenger",
    model=Ollama(id="llama3.2"),
    tools=[DiscordTools()],
    show_tool_calls=True,
    markdown=True,
)

playground_app = Playground(agents=[web_agent, discord_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve(app, host="0.0.0.0", port=7778)