import os
import asyncio
import aiohttp
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger

async def ollama_llm(prompt, model="llama3", **kwargs):
    """Generate text using a local Ollama model."""
    import aiohttp
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result.get("response", "")

async def ollama_embed(text, model="nomic-embed-text"):
    """Generate embeddings using a local Ollama model."""
    url = "http://localhost:11434/api/embeddings"
    payload = {
        "model": model,
        "input": text
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result.get("embedding", [])

setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

import aiohttp

class OllamaEmbedding:
    def __init__(self, model="nomic-embed-text", dim=768):
        self.model = model
        self.embedding_dim = dim

    async def __call__(self, texts):
        # Accept either single string or list of strings
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        url = "http://localhost:11434/api/embeddings"

        async with aiohttp.ClientSession() as session:
            for text in texts:
                text = text.strip()
                if not text:
                    # Return zero vector if empty input
                    embeddings.append([0.0] * self.embedding_dim)
                    continue

                payload = {
                    "model": self.model,
                    "input": text
                }
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        emb = result.get("embedding")
                        if emb and len(emb) == self.embedding_dim:
                            embeddings.append(emb)
                        else:
                            # Fallback to zero vector if missing or wrong size
                            embeddings.append([0.0] * self.embedding_dim)
                    else:
                        # HTTP error fallback
                        embeddings.append([0.0] * self.embedding_dim)

        return embeddings

async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=OllamaEmbedding(model="nomic-embed-text", dim=768),
        llm_model_func=ollama_llm
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

async def main():
    rag = None   # <— Prevents UnboundLocalError
    try:
        rag = await initialize_rag()
        # ... rest of your code ...
        await rag.initialize_storages()
        await initialize_pipeline_status()
        # await rag.ainsert(
        #     """
        #     Product Name: The Awesome Super Device
        #     Developers: Daniel X's Fictional Item Manufacturing Company
        #     Dimensions: 1ft x 1ft x 1ft
        #     Available colors: Red, blue, green, purple, silver, gold
        #     Description: A solid cube of an unknown material. There are no visible patterns on its surface.
        #     Purpose: To sit around looking cool inside a person's room. It serves no actual function.
        #     """
        # )

        # Perform hybrid search
        mode = "hybrid"
        print(
          await rag.aquery(
              "What does the Awesome Super Device do?",
              param=QueryParam(mode=mode)
          )
        )

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())