from flask import Flask, request, jsonify
import numpy as np
import faiss
import json
import os
from logic import process_query_with_gemini, CACHE_EMBEDDINGS_PATH, CACHE_CHUNKS_PATH

app = Flask(__name__)

print("Loading knowledge base for the server...")
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    embeddings_path = os.path.join(base_dir, '..', CACHE_EMBEDDINGS_PATH)
    chunks_path = os.path.join(base_dir, '..', CACHE_CHUNKS_PATH)
    embeddings = np.load(embeddings_path)
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    print("Knowledge base loaded successfully into memory.")
except FileNotFoundError:
    index = None
    chunks = None
    print("FATAL SERVER ERROR: Pre-built knowledge base files not found.")

@app.route('/api/process', methods=['POST'])
def process_claim_endpoint():
    if index is None:
        return jsonify({"error": "Knowledge base not loaded on the server."}), 500
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

# DO NOT ADD THE if __name__ == '__main__' BLOCK HERE. THE FILE ENDS HERE.