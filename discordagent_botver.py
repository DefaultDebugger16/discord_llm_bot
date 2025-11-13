import os
import discord
import re
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.mcp import MCPTools
from googlesearch2 import GoogleSearchTools2

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True

# Initialize Discord client
client = discord.Client(intents=INTENTS)

@client.event
async def on_ready():
    print(f"Bot connected as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.reference is not None:
        return
    if client.user not in message.mentions:
        return

    user_id = str(message.author.id)
    username = str(message.author.name)

    # Prepend metadata to the message
    prompt = f"<user id='{user_id}' username='{username}'>\n{message.content}"

    async with MCPTools(transport="streamable-http", url="http://localhost:8505/mcp", timeout_seconds=45) as mcp_tools:
        discord_agent = Agent(
            name="Discord Agent",
            model=Ollama(id="qwen3:8b"),
            tools=[mcp_tools],
            instructions=[
                """
                When completing multi-step tasks, always break the task into steps, and at each step:
                - Describe what you are doing.
                - If a tool is needed, invoke it.
                - Then, after the tool output, summarize what was learned before proceeding to the next step.

                Repeat this loop until the task is complete.
                """
            ],
            storage=SqliteStorage(table_name="web_agent", db_file="tmp/agents.db"),
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=5,
            
            markdown=True,
        )

        # Process message via Agno agent
        response = await discord_agent.arun(prompt, intermediate_tool_outputs=True)

    # Split response into thinking and visible content
    content = response.content
    thinking_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    visible = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    print(f"[THOUGHT PROCESS]: {thinking}")

    # Send visible response in chunks
    MAX_DISCORD_MESSAGE_LENGTH = 2000
    for i in range(0, len(visible), MAX_DISCORD_MESSAGE_LENGTH):
        chunk = visible[i:i + MAX_DISCORD_MESSAGE_LENGTH]
        await message.channel.send(chunk)

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)