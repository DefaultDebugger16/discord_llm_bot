import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed, gpt_4o_mini_complete
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger

# Optional logging
setup_logger("lightrag", level="INFO")

WORKING_DIR = "rag_storage"
os.makedirs(WORKING_DIR, exist_ok=True)

async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()           # Step 1
    await initialize_pipeline_status()        # Step 2 (needed to avoid UnboundLocalError)
    return rag

async def main():
    file_path = os.path.join(WORKING_DIR, "testproduct.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        document_content = f.read().strip()

    if not document_content:
        raise ValueError("Document content is empty — LightRAG needs non-empty text to index.")

    rag = await initialize_rag()

    # Async insert
    await rag.ainsert(document_content)

    # Query example
    response = await rag.aquery(
        "What is the Awesome Super Device?",
        param=QueryParam(mode="hybrid")
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
