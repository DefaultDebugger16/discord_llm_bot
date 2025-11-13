from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
agent_storage: str = "tmp/agents.db"
# llama_local_model.py
import requests
from typing import List
from agno.models.base import Model
from types import SimpleNamespace
import aiohttp
import asyncio
'''
class Message:
    def __init__(self, role: str, content: str, thinking: str = "dot dot"):
        print(f"[Message created] role={role}, content={repr(content)}, thinking={thinking}")
        self.role = role
        self.content = content
        self.thinking = thinking

class LLaMALocal(Model):
    id = "llama3-local"
    provider = "ollama"

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def _get_role(self, msg):
        return getattr(msg, "role", None)

    def _get_content(self, msg):
        return getattr(msg, "content", None)

    def _format_messages(self, messages: List[dict]):
        return [{"role": "system", "content": "You are a helpful assistant."}] + [
            {"role": self._get_role(msg), "content": self._get_content(msg)}
            for msg in messages
            if self._get_role(msg) in ["user", "assistant"]
        ]

    def invoke(self, messages: List[dict], **kwargs) -> str:
        formatted_messages = self._format_messages(messages)
        response = requests.post(
            f"{self.host}/api/chat",
            json={"model": self.model, "messages": formatted_messages},
        )
        data = response.json()
        return data["message"]["content"]

    async def ainvoke(self, messages: List[dict], **kwargs) -> str:
        #return self.invoke(messages, **kwargs)
        print("Returning fake response from ainvoke")
        return SimpleNamespace(role="assistant", content="Hello from ainvoke")

    async def ainvoke_stream(self, messages: List[dict], **kwargs):
        formatted_messages = self._format_messages(messages)
        print("Sending request to Ollama...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": formatted_messages, "stream": True},
            ) as resp:
                async for line in resp.content:
                    try:
                        text = line.decode("utf-8").strip()
                        # print("RAW LINE:", text)

                        if not text.startswith("data: "):
                            continue
                        payload = text[len("data: "):]
                        if payload == "[DONE]":
                            break

                        data = json.loads(payload)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            print("Yielding chunk:", chunk)
                            yield {"role": "assistant", "content": chunk}  # ✅ fixed
                    except Exception as e:
                        print("Stream decode error:", e)
                        continue

    def invoke_stream(self, messages: List[dict], **kwargs):
        raise NotImplementedError("Sync streaming not supported")

    def parse_provider_response(self, response, **kwargs):
        return response

    def parse_provider_response_delta(self, delta, **kwargs):
        return delta

class FakeModel(Model):
    id = "fake-model"
    provider = "test"

    def __init__(self, model: str = "fake-model"):
        self.model = model

    async def ainvoke_stream(self, messages, **kwargs):
        for part in ["Hello ", "from ", "LLaMA!"]:
            await asyncio.sleep(0.2)
            yield Message(role="assistant", content=part, thinking="[erm1]")
        yield Message(role="assistant", content="", thinking="[erm2]")

    async def ainvoke(self, messages, **kwargs):
        return Message(role="assistant", content="Example response", thinking="[erm (ainvoke)]")

    def invoke(self, messages: List[dict], **kwargs) -> str:
        return "Sync response not used"

    def invoke_stream(self, messages: List[dict], **kwargs):
        raise NotImplementedError("Sync streaming not supported")

    def parse_provider_response(self, response, **kwargs):
        return response

    def parse_provider_response_delta(self, delta, **kwargs):
        return delta  # Don't unwrap content here
'''
web_agent = Agent(
    name="Web Agent",
    model=Ollama(id="llama3"), #model=LLaMALocal(model="llama3"),
    tools=[DuckDuckGoTools()],
    instructions=["Always include sources"],
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

finance_agent = Agent(
    name="Finance Agent",
    model=FakeModel(model="llama3"), #model=LLaMALocal(model="llama3"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True)],
    instructions=["Always use tables to display data"],
    storage=SqliteStorage(table_name="finance_agent", db_file=agent_storage),
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=5,
    markdown=True,
)

playground_app = Playground(agents=[web_agent, finance_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve(app, host="0.0.0.0", port=7777)