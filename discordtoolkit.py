"""Discord integration tools for interacting with Discord channels and servers."""

import json
from os import getenv
from typing import Any, Dict, List, Optional

import requests

from agno.tools import Toolkit
from agno.utils.log import logger

import calendar
from datetime import datetime, timedelta
import discord
from discord import Permissions

class DiscordTools2(Toolkit):
    def __init__(
        self,
        client: discord.Client,
        bot_token: Optional[str] = None,
        enable_messaging: bool = True,
        enable_history: bool = True,
        enable_channel_management: bool = True,
        enable_message_management: bool = True,
        **kwargs,
    ):
        self.client=client
        self.bot_token = bot_token or getenv("DISCORD_BOT_TOKEN")
        if not self.bot_token:
            logger.error("Discord bot token is required")
            raise ValueError("Discord bot token is required")

        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
        }

        tools: List[Any] = []
        if enable_messaging:
            tools.append(self.send_message)
        if enable_history:
            tools.append(self.get_channel_messages)
        if enable_channel_management:
            tools.append(self.get_channel_info)
            tools.append(self.list_channels)
        if enable_message_management:
            tools.append(self.delete_message)
            tools.append(self.timeout_member)

        super().__init__(name="discord", tools=tools, **kwargs)

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to Discord API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json() if response.text else {}

    def send_message(self, channel_id: str, message: str) -> str:
        """
        Send a message to a Discord channel.

        Args:
            channel_id (int): The ID of the channel to send the message to.
            message (str): The text of the message to send.

        Returns:
            str: A success message or error message.
        """
        try:
            data = {"content": message}
            self._make_request("POST", f"/channels/{int(channel_id)}/messages", data)
            return f"Message sent successfully to channel {channel_id}"
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return f"Error sending message: {str(e)}"

    def get_channel_info(self, channel_id: str) -> str:
        """
        Get information about a Discord channel.

        Args:
            channel_id (int): The ID of the channel to get information about.

        Returns:
            str: A JSON string containing the channel information.
        """
        try:
            response = self._make_request("GET", f"/channels/{int(channel_id)}")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return f"Error getting channel info: {str(e)}"

    def list_channels(self, guild_id: str) -> str:
        """
        List all channels in a Discord server.

        Args:
            guild_id (int): The ID of the server to list channels from.

        Returns:
            str: A JSON string containing the list of channels.
        """
        try:
            response = self._make_request("GET", f"/guilds/{int(guild_id)}/channels")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return f"Error listing channels: {str(e)}"

    def utc_to_snowflake(self, year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
        discord_epoch = 1420070400000
        dt = datetime(year, month, day, hour, minute)
        timestamp = calendar.timegm(dt.timetuple())
        return (int(timestamp * 1000) - discord_epoch) << 22

    def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100,
        start_year: int = None,
        start_month: int = None,
        start_day: int = None,
        start_hour: int = 0,
        start_minute: int = 0,
        end_year: int = None,
        end_month: int = None,
        end_day: int = None,
        end_hour: int = 0,
        end_minute: int = 0
    ) -> str:
        """
        Get the message history of a Discord channel. The two start and end UTC timestamps are optional.

        Returns:
            str: A JSON string containing the channel's message history.
        """
        try:
            params = [f"limit={limit}"]

            # Only generate snowflake if full date is provided
            if all(v is not None for v in [start_year, start_month, start_day]):
                after_id = self.utc_to_snowflake(start_year, start_month, start_day, start_hour, start_minute)
                params.append(f"after={after_id}")

            if all(v is not None for v in [end_year, end_month, end_day]):
                before_id = self.utc_to_snowflake(end_year, end_month, end_day, end_hour, end_minute)
                params.append(f"before={before_id}")

            query_string = "&".join(params)
            response = self._make_request("GET", f"/channels/{int(channel_id)}/messages?{query_string}")
            return json.dumps(response, indent=2)

        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return f"Error getting messages: {str(e)}"

    """def get_channel_messages(self, channel_id: str, limit: int = 100) -> str:
        
        Get the message history of a Discord channel.

        Args:
            channel_id (int): The ID of the channel to fetch messages from.
            limit (int): The maximum number of messages to fetch. Defaults to 100.

        Returns:
            str: A JSON string containing the channel's message history.
        
        try:
            response = self._make_request("GET", f"/channels/{int(channel_id)}/messages?limit={limit}")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return f"Error getting messages: {str(e)}" """

    def delete_message(self, channel_id: str, message_id: str) -> str:
        """
        Delete a message from a Discord channel.

        Args:
            channel_id (int): The ID of the channel containing the message.
            message_id (int): The ID of the message to delete.

        Returns:
            str: A success message or error message.
        """
        try:
            self._make_request("DELETE", f"/channels/{int(channel_id)}/messages/{int(message_id)}")
            return f"Message {message_id} deleted successfully from channel {channel_id}"
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return f"Error deleting message: {str(e)}"

    async def timeout_member(self, guild_id: str, user_id: str, duration_seconds: int, actor_id: str):
        guild = self.client.get_guild(int(guild_id))
        if guild is None:
            guild = await self.client.fetch_guild(int(guild_id))

        actor = guild.get_member(int(actor_id))
        if actor is None:
            try:
                actor = await guild.fetch_member(int(actor_id))
            except discord.NotFound:
                return f"Actor {actor_id} not found in guild {guild_id}"

        # Check if actor has the 'Moderate Members' permission
        perms = actor.guild_permissions
        if not perms.moderate_members:
            return f"User {actor_id} does not have permission to timeout members."

        member = guild.get_member(int(user_id))
        if member is None:
            try:
                member = await guild.fetch_member(int(user_id))
            except discord.NotFound:
                return f"Member {user_id} not found in guild {guild_id}"
        
        until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
        await member.timeout(until)
        return f"Timed out user {user_id} for {duration_seconds} seconds."

    @staticmethod
    def get_tool_name() -> str:
        """Get the name of the tool."""
        return "discord"

    @staticmethod
    def get_tool_description() -> str:
        """Get the description of the tool."""
        return "Tool for interacting with Discord channels and servers"

    @staticmethod
    def get_tool_config() -> dict:
        """Get the required configuration for the tool."""
        return {
            "bot_token": {"type": "string", "description": "Discord bot token for authentication", "required": True}
        }
if __name__ == "__main__":
    mcp.run(transport='stdio')