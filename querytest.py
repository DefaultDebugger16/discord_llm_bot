import asyncio
import requests # Import the requests library for HTTP calls
import json # For handling JSON data

# --- Configuration ---
# Define the LightRAG server URL
LIGHTRAG_SERVER_URL = "http://localhost:9621"

# --- Main Asynchronous Function ---
async def main():
    print(f"Connecting to LightRAG server at: {LIGHTRAG_SERVER_URL}")

    # --- Prepare Content ---
    sample_text = """
    The quick brown fox jumps over the lazy dog. This sentence is often used to test typewriters
    and computer keyboards because it contains all letters of the English alphabet.
    The fox is known for its cunning, and the dog is a common domestic animal.
    Vector databases store numerical representations of text, images, or other data,
    enabling fast similarity searches. LightRAG extends this by building knowledge graphs.
    """

    # --- Insert Content via Server API ---
    #print("\nInserting sample content via LightRAG server...")
    insert_url = f"{LIGHTRAG_SERVER_URL}/documents/text" # Endpoint for inserting text
    headers = {"Content-Type": "application/json"}
    payload = {"text": sample_text}
    
    # try:
    #     response = requests.post(insert_url, headers=headers, data=json.dumps(payload))
    #     response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    #     print("Content inserted successfully via server!")
    #     print(f"Server response: {response.json()}")
    # except requests.exceptions.ConnectionError:
    #     print(f"Error: Could not connect to LightRAG server at {LIGHTRAG_SERVER_URL}.")
    #     print("Please ensure 'lightrag-server' is running on port 9621.")
    #     return
    # except requests.exceptions.HTTPError as err:
    #     print(f"HTTP error occurred during insertion: {err}")
    #     print(f"Server responded with: {response.text}")
    #     return
    # except Exception as e:
    #     print(f"An unexpected error occurred during insertion: {e}")
    #     return

    # --- Perform a Query via Server API ---
    query_text = "What is the width of a 2025 Tesla Model Y in millimeters when the mirrors are folded?"
    print(f"\nQuerying LightRAG server: '{query_text}'")
    query_url = f"{LIGHTRAG_SERVER_URL}/query" # Endpoint for querying
    query_payload = {
        "query": query_text,
        "mode": "naive" # Match the mode you want to use on the server
    }

    try:
        response = requests.post(query_url, headers=headers, data=json.dumps(query_payload))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print("\n--- Query Response from Server ---")
        print(response.json()) # Server response will likely be JSON
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to LightRAG server at {LIGHTRAG_SERVER_URL}.")
        print("Please ensure 'lightrag-server' is running on port 9621.")
        return
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred during query: {err}")
        print(f"Server responded with: {response.text}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during query: {e}")
        return

# --- Run the main asynchronous function ---
if __name__ == "__main__":
    asyncio.run(main())