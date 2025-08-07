import numpy as np
import faiss
import google.generativeai as genai
import json
import os

# This file contains the core processing logic using the Google Gemini API.

# --- Configuration ---
# The API key will be loaded from the environment variables.
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
except (ValueError, Exception) as e:
    print(f"Warning: Could not configure Gemini API. Error: {e}")

# Model and cache file paths
EMBEDDING_MODEL = 'models/text-embedding-004'
LLM_MODEL = "gemini-2.5-flash-lite"
DOCUMENT_PATH = "policy_document.txt"
CACHE_EMBEDDINGS_PATH = "policy_embeddings_gemini.npy"
CACHE_CHUNKS_PATH = "policy_chunks_gemini.json"

# --- Function Definitions ---

def load_and_chunk_document():
    """Loads and chunks the policy document from the hardcoded path."""
    with open(DOCUMENT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    return [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]

def create_embeddings_and_save(chunks):
    """Creates embeddings using Gemini and saves them to local files."""
    print(f"Creating embeddings with Gemini model: {EMBEDDING_MODEL}...")
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings_np = np.array(result['embedding'])
        
        np.save(CACHE_EMBEDDINGS_PATH, embeddings_np)
        with open(CACHE_CHUNKS_PATH, 'w', encoding='utf-8') as f:
            json.dump(chunks, f)
        print(f"Successfully created and saved '{CACHE_EMBEDDINGS_PATH}' and '{CACHE_CHUNKS_PATH}'.")
        return True
    except Exception as e:
        print(f"FATAL ERROR while creating embeddings: {e}")
        return False

def process_query_with_gemini(query, index, chunks):
    """The main RAG processing function for a single query."""
    print(f"Processing query: '{query}'")
    query_embedding_result = genai.embed_content(model=EMBEDDING_MODEL, content=query, task_type="RETRIEVAL_QUERY")
    query_embedding = query_embedding_result['embedding']
    
    distances, indices = index.search(np.array([query_embedding]), 3)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    context_clauses = "\n---\n".join(retrieved_chunks)

    prompt = f"""You are an expert insurance claims processor. Evaluate the user's claim based on their query and the provided policy clauses. **User's Query:** "{query}" **Relevant Policy Clauses:** --- {context_clauses} --- **Instructions:** 1. Analyze the query. 2. Review only the provided clauses. 3. Decide "Approved" or "Rejected". 4. Justify your decision, mapping it to the clauses. 5. If rejected, amount is 0. If approved, state amount depends on rates. 6. Output MUST be valid JSON only. **JSON Format:** {{"Decision": "...", "Amount": "...", "Justification": [{{"Reasoning": "...", "SupportingClause": "..."}}]}}"""
    
    model = genai.GenerativeModel(LLM_MODEL, generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(prompt)
    return response.text