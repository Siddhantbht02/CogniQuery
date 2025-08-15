from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import sys         
from werkzeug.utils import secure_filename
from dotenv import load_dotenv 
from subprocess import run 

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads' # For local testing
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure uploads folder exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Use current Python interpreter
PYTHON_EXECUTABLE = sys.executable
PYTHON_WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logic.py') # logic.py is the worker script


# --- Helper function to run the Python worker (logic.py) ---
def run_python_worker(mode, query=None, file_path=None):
    cmd = [PYTHON_EXECUTABLE, PYTHON_WORKER_SCRIPT, '--mode', mode]
    if query:
        cmd.extend(['--query', query])
    if file_path:
        cmd.extend(['--file', os.path.abspath(file_path)]) # Pass absolute path to worker
    
    # Pass GOOGLE_API_KEY from current env to the subprocess env
    env_vars = os.environ.copy()
    if 'GOOGLE_API_KEY' not in env_vars and os.getenv('GOOGLE_API_KEY'):
        env_vars['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
    
    print(f"Executing Python worker: {' '.join(cmd)}", file=sys.stderr) # <--- FIXED
    result = run(cmd, capture_output=True, text=True, env=env_vars)
    
    if result.returncode != 0:
        print(f"Python worker failed (Mode: {mode}):", file=sys.stderr) # <--- FIXED
        print(f"Stdout: {result.stdout}", file=sys.stderr) # <--- FIXED
        print(f"Stderr: {result.stderr}", file=sys.stderr) # <--- FIXED
        raise Exception(f"Python worker error: {result.stderr or result.stdout}")
    
    return result.stdout.strip()


# --- Check for Pre-built Knowledge Base Files on App Startup ---
# These paths are relative to the project root where app.py is located.
print("Checking for pre-built knowledge base files...", file=sys.stderr) # <--- FIXED
prebuilt_embeddings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base.npy')
prebuilt_chunks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base_chunks.json')


if not os.path.exists(prebuilt_embeddings_path) or not os.path.exists(prebuilt_chunks_path):
    print("WARNING: Pre-built knowledge base files (knowledge_base.npy/.json) NOT FOUND in root directory.", file=sys.stderr) # <--- FIXED
    print("         The /api/process endpoint will attempt to run, but may fail if the Python worker cannot load them.", file=sys.stderr) # <--- FIXED
    print("         Run the build command first: `python logic.py --mode build_kb`", file=sys.stderr) # <--- FIXED
else:
    print("Pre-built knowledge base files found.", file=sys.stderr) # <--- FIXED


# --- API Endpoint 1: Query Pre-built Knowledge Base ---
@app.route('/api/process', methods=['POST'])
def query_prebuilt_kb_endpoint():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({"error": "Bad Request: Missing 'query' in request body."}), 400

    try:
        # Call the logic.py worker in prebuilt_kb mode
        response_text = run_python_worker('test_prebuilt_kb', query=query)
        response_json = json.loads(response_text)
        return jsonify(response_json)
    except Exception as e:
        print(f"Error during pre-built query processing: {e}", file=sys.stderr) # <--- FIXED
        return jsonify({"error": "An internal error occurred during query processing.", "details": str(e)}), 500


# --- API Endpoint 2: File Upload and On-the-Fly Processing ---
@app.route('/api/process-upload', methods=['POST'])
def process_upload_endpoint():
    if 'file' not in request.files or 'query' not in request.form:
        return jsonify({"error": "Bad Request: Missing 'file' or 'query' in the request. Ensure you're sending form-data."}), 400

    file = request.files['file']
    query = request.form['query']

    if file.filename == '':
        return jsonify({"error": "Bad Request: No selected file. Filename is empty."}), 400

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    filename = secure_filename(file.filename)
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(temp_file_path)
        print(f"File saved to temporary path: {temp_file_path}", file=sys.stderr) # <--- FIXED

        # Call the logic.py worker in on_the_fly mode
        response_text = run_python_worker('test_on_the_fly', query=query, file_path=temp_file_path)
        
        response_json = json.loads(response_text)
        return jsonify(response_json)

    except Exception as e:
        print(f"Error during on-the-fly processing: {e}", file=sys.stderr) # <--- FIXED
        return jsonify({"error": "An internal server error occurred during document processing.", "details": str(e)}), 500
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Cleaned up temporary file: {temp_file_path}", file=sys.stderr) # <--- FIXED


# --- Frontend Serving Route ---
@app.route('/')
def serve_frontend():
    # Serve index.html from the 'public' folder
    # Assuming public/ is directly in the root
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public'), 'index.html')


# --- Local Development Server Entry Point ---
if __name__ == '__main__':
    load_dotenv() # Load .env for local run

    api_key_local = os.getenv('GOOGLE_API_KEY')
    if not api_key_local:
        print("FATAL ERROR: GOOGLE_API_KEY not found in .env file for local run. Please set it.", file=sys.stderr) # <--- FIXED
        exit(1)
    
    print("API key loaded. Starting Flask development server...", file=sys.stderr) # <--- FIXED
    print("NOTE: This Flask app is the Python part of your hybrid backend. It's invoked by Node.js.", file=sys.stderr) # <--- FIXED
    print("      To run the full local server (Node.js + Python), please execute `npm start` in the main project directory.", file=sys.stderr) # <--- FIXED
    app.run(debug=True, port=5000)