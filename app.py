from flask import Flask, request, jsonify
import numpy as np
import faiss
import json
import os
from logic import process_query_with_gemini, CACHE_EMBEDDINGS_PATH, CACHE_CHUNKS_PATH

app = Flask(__name__)

# --- Load the pre-built knowledge base with extra debugging ---
print("--- Server Startup ---")
print(f"Current Working Directory: {os.getcwd()}") # This tells us where the script is running from

try:
    # We will now use absolute paths to be 100% certain
    project_root = os.path.dirname(os.path.abspath(__file__))
    embeddings_path = os.path.join(project_root, CACHE_EMBEDDINGS_PATH)
    chunks_path = os.path.join(project_root, CACHE_CHUNKS_PATH)

    print(f"Attempting to load knowledge base from:")
    print(f"  - Embeddings: {embeddings_path}")
    print(f"  - Chunks: {chunks_path}")

    embeddings = np.load(embeddings_path)
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    print("Knowledge base loaded successfully into memory.")

except FileNotFoundError:
    index = None
    chunks = None
    print("\nFATAL SERVER ERROR: Pre-built knowledge base files NOT FOUND at the expected location.")
    print("Please run 'python build_index.py' in the project's root directory to generate them.\n")

# ... (The rest of your app.py file is unchanged) ...
@app.route('/api/process', methods=['POST'])
def process_claim_endpoint():
    if index is None:
        return jsonify({"error": "Knowledge base not loaded on the server. Please check the server logs for the file path error."}), 500
    # ... (rest of the function is the same)
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Bad Request: Missing 'query' in request body."}), 400
    query = data['query']
    try:
        response_text = process_query_with_gemini(query, index, chunks)
        response_json = json.loads(response_text)
        return jsonify(response_json)
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": "An internal error occurred.", "details": str(e)}), 500

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv('GOOGLE_API_KEY'):
        print("FATAL ERROR: GOOGLE_API_KEY not found in .env file.")
    else:
        print("API key loaded. Starting Flask development server...")
        app.run(debug=True, port=5000)

