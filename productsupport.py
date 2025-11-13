import os
import re
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.tools.googlesearch import GoogleSearchTools
import discord
from discord.ext import commands
from discord.ui import View, Button
from pstools import ProductSupportTools
from discordtoolkit import DiscordTools2

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

discord_agent = Agent(
    name="Discord Agent",
    model=Ollama(id="qwen3"),
    tools=[ProductSupportTools(rag_api_url="http://localhost:9621/query"), DiscordTools2(DISCORD_TOKEN)],
    instructions=[
        """
        """
    ],
    storage=SqliteStorage(table_name="web_agent", db_file="tmp/agents.db"),
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=5,
    markdown=True,
)

class CreateChannelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Private Chat", style=discord.ButtonStyle.green, custom_id="create_channel_button")
    async def create_channel(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user

        # Replace with your actual moderator role ID
        # moderator_role_id = 987654321098765432
        # moderator_role = guild.get_role(moderator_role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            # moderator_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel_name = f"{user.name.lower().replace(' ', '-')}-chat"

        category_id = 1397670173238100019  # Replace with your category ID
        category = discord.utils.get(guild.categories, id=category_id)

        new_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category
        )

        await new_channel.send("Hello! You created a new support channel. Feel free to ask any questions about our products!")

        await interaction.response.send_message(f"Channel created: {new_channel.mention}", ephemeral=True)
"""
@bot.tree.command(name="ping", description="Replies \"pong.\"")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")
"""
@bot.tree.command(name="delete_channel", description="Delete this private chat channel")
async def delete(interaction: discord.Interaction):
    user = interaction.user
    channel = interaction.channel
    guild = interaction.guild

    # Only allow in private chat channels
    if not channel.name.endswith("-chat"): # THIS IS NOT A VERY GOOD CRITERIA FOR CHANNEL DELETION. FIND A BETTER MARKER FOR SUPPORT CHANNELS
        await interaction.response.send_message("This command can only be used in private chat channels.", ephemeral=True)
        return

    # Replace with your actual moderator role ID
    #moderator_role_id = 987654321098765432
    #moderator_role = guild.get_role(moderator_role_id)

    # Check if user is allowed to delete
    allowed = (
        channel.permissions_for(user).manage_channels #or
        #moderator_role in user.roles
    )

    if not allowed:
        await interaction.response.send_message("You don't have permission to delete this channel.", ephemeral=True)
        return

    view = DeleteConfirmationView(author=user)
    await interaction.response.send_message(
        "Are you sure you want to delete this channel?",
        view=view,
        ephemeral=True
    )
    
from discord.ui import View, button

class DeleteConfirmationView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=30)  # auto-timeout after 30 seconds
        self.author = author

    @button(label="✅ Yes, delete", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Only the original requester can confirm.", ephemeral=True)
            return

        await interaction.response.send_message("Deleting channel...", ephemeral=True)
        await interaction.channel.delete()

    @button(label="❌ Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Only the original requester can cancel.", ephemeral=True)
            return

        await interaction.response.send_message("Channel deletion canceled.", ephemeral=True)
        self.stop()

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.tree.sync()
    print(f"Bot connected as {bot.user}")

    # Send the embed to a specific channel
    channel_id = 1397670208331845702  # Your embed channel
    channel = bot.get_channel(channel_id)

    if channel:
        embed = discord.Embed(
            title="Start a Chat",
            description="Click the button below to create a private channel where I can assist you!",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CreateChannelView())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Optional: Skip if not in a generated private channel
    if not message.channel.name.endswith("-chat"):
        return

    user_id = str(message.author.id)
    username = str(message.author.name)

    prompt = f"<user id='{user_id}' username='{username}'>\n{message.content}"
    response = await discord_agent.arun(prompt, intermediate_tool_outputs=True)

    content = response.content
    thinking_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    visible = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    print(f"[THOUGHT PROCESS]: {thinking}")

    MAX_DISCORD_MESSAGE_LENGTH = 2000
    for i in range(0, len(visible), MAX_DISCORD_MESSAGE_LENGTH):
        chunk = visible[i:i + MAX_DISCORD_MESSAGE_LENGTH]
        await message.channel.send(chunk)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)