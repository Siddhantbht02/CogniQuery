from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import faiss
import json
import os
# Werkzeug is a Flask dependency, used here for secure filenames
from werkzeug.utils import secure_filename

# Import ALL the logic functions now
from logic import (
    process_query_with_gemini, 
    process_single_file_and_query, # Our new function
    CACHE_EMBEDDINGS_PATH, 
    CACHE_CHUNKS_PATH
)

# Initialize the Flask app and apply CORS
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Create a folder to temporarily store uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# --- Load the PRE-BUILT knowledge base ONCE when the server starts ---
# (This part is unchanged)
print("Loading pre-built knowledge base for the server...")
try:
    embeddings = np.load(CACHE_EMBEDDINGS_PATH)
    with open(CACHE_CHUNKS_PATH, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    prebuilt_index = faiss.IndexFlatL2(embeddings.shape[1])
    prebuilt_index.add(embeddings)
    prebuilt_chunks = chunks
    print("Pre-built knowledge base loaded successfully.")
except FileNotFoundError:
    prebuilt_index = None
    prebuilt_chunks = None
    print("WARNING: Pre-built knowledge base not found. The /api/process endpoint will not work.")


# --- Endpoint 1: For the PRE-BUILT knowledge base (No Change) ---
@app.route('/api/process', methods=['POST'])
def process_claim_endpoint():
    if prebuilt_index is None:
        return jsonify({"error": "Pre-built knowledge base not loaded on the server."}), 500
    data = request.get_json()
    query = data.get('query')
    # ... (rest of this function is the same)
    # ... use process_query_with_gemini(query, prebuilt_index, prebuilt_chunks)


# --- Endpoint 2: NEW Endpoint for file uploads ---
@app.route('/api/process-upload', methods=['POST'])
def process_upload_endpoint():
    if 'file' not in request.files or 'query' not in request.form:
        return jsonify({"error": "Bad Request: Missing 'file' or 'query' in the request."}), 400

    file = request.files['file']
    query = request.form['query']

    if file.filename == '':
        return jsonify({"error": "Bad Request: No selected file."}), 400

    if file:
        # Secure the filename to prevent security issues
        filename = secure_filename(file.filename)
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save the file temporarily
            file.save(temp_file_path)
            
            # Call our new logic function that does the full on-the-fly pipeline
            response_text = process_single_file_and_query(temp_file_path, query)
            response_json = json.loads(response_text)
            return jsonify(response_json)
            
        except Exception as e:
            print(f"Error during on-the-fly processing: {e}")
            return jsonify({"error": "An internal error occurred during file processing.", "details": str(e)}), 500
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return jsonify({"error": "An unknown error occurred."}), 500


# --- The runnable block is also the same ---
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv('GOOGLE_API_KEY'):
        print("FATAL ERROR: GOOGLE_API_KEY not found.")
    else:
        print("API key loaded. Starting Flask development server...")
        app.run(debug=True, port=5000)