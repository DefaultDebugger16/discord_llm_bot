"""Discord integration tools for interacting with Discord channels and servers."""

import random
import json
from os import getenv
from typing import Any, Dict, List, Optional

import requests

from agno.tools import Toolkit
from agno.utils.log import logger
import aiohttp

class ProductSupportTools(Toolkit):
    def __init__(self, rag_api_url: str, testing: bool = True, **kwargs):
        self.headers = {
            "Content-Type": "application/json",
        }
        self.rag_api_url = rag_api_url  # e.g. "http://localhost:8000/query"
        
        tools: List[Any] = []
        if testing:
            tools.append(self.coinflip)
            tools.append(self.query_rag)

        super().__init__(name="discord", tools=tools, **kwargs)

    async def coinflip(self) -> str:
        coin = random.randint(0, 1)
        return "Heads" if coin == 1 else "Tails"

    async def query_rag(self, query: str) -> str:
        """
        Query the LightRAG server via REST API.

        Args:
            query (str): The natural language question to send

        Returns:
            str: The response text from the RAG server
        """
        print(f"QUERY:\n{query}\n----------------------------")
        payload = {
            "query": query,
            "mode": "naive"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.rag_api_url, json=payload, headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"RAG RESPONSE:\n{data}\n---------------------------")
                    # Adjust based on your API response structure
                    return data.get("answer") or data.get("response") or json.dumps(data)
                else:
                    return f"Error querying RAG server: HTTP {resp.status}"
