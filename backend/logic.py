import numpy as np
import faiss
import google.generativeai as genai
import json
import os
import sys  # For sys.stderr
import docx  # python-docx for DOCX
import argparse # For command-line arguments
from dotenv import load_dotenv # For direct build_kb run

# --- NEW PDF LIBRARIES ---
import pdfplumber 
from pdfminer.high_level import extract_text as pdfminer_extract_text # Fallback/alternative
# --- End NEW PDF LIBRARIES ---

# --- Configuration ---
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Warning: GOOGLE_API_KEY not found in environment variables upon logic.py import.", file=sys.stderr)
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    print(f"ERROR: Could not configure Gemini API. Details: {e}", file=sys.stderr)
    exit(1)

# Model and paths
EMBEDDING_MODEL = 'models/text-embedding-004'
LLM_MODEL = "gemini-2.5-flash-lite"
SOURCE_DOCS_PATH = "source_documents"
CACHE_EMBEDDINGS_PATH = "knowledge_base.npy"
CACHE_CHUNKS_PATH = "knowledge_base_chunks.json"

# --- Text Extraction Helpers (UPDATED for PDF) ---

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or "" # extract_text might return None
        return text
    except Exception as e:
        # Fallback to pdfminer.high_level in case pdfplumber has issues
        print(f"Warning: pdfplumber failed ({e}). Attempting pdfminer.high_level for {file_path}", file=sys.stderr)
        try:
            return pdfminer_extract_text(file_path)
        except Exception as fallback_e:
            raise Exception(f"Failed to extract text from PDF {file_path} with both pdfplumber and pdfminer.high_level: {fallback_e}")


def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file, paragraph by paragraph."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path):
    """Extracts text from a plain text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# --- Smart Chunking Strategy (Unchanged) ---
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    if len(text) <= chunk_size: return [text]
    chunks = []; start = 0
    while start < len(text):
        end = start + chunk_size; chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

# --- Document Loading & Chunking from directory (Unchanged, calls new extractors) ---
def load_and_chunk_documents(source_path=SOURCE_DOCS_PATH):
    print(f"Loading documents from directory: {source_path}", file=sys.stderr)
    all_chunks = []
    if not os.path.exists(source_path):
        print(f"Error: Directory not found at '{source_path}'. Please create and place documents.", file=sys.stderr)
        return all_chunks
    for filename in os.listdir(source_path):
        file_path = os.path.join(source_path, filename)
        if not os.path.isfile(file_path): continue
        print(f"--> Processing file: {filename}", file=sys.stderr)
        full_text = "";
        try:
            if filename.lower().endswith('.pdf'): full_text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith('.docx'): full_text = extract_text_from_docx(file_path)
            elif filename.lower().endswith('.txt'): full_text = extract_text_from_txt(file_path)
            else: print(f"    Unsupported file type: {filename}. Skipping.", file=sys.stderr); continue
            chunks = chunk_text(full_text); all_chunks.extend(chunks);
            print(f"    Extracted and split into {len(chunks)} chunks.", file=sys.stderr)
        except Exception as e: print(f"    Error processing file {filename}: {e}. Skipping.", file=sys.stderr)
    print(f"Successfully processed all files into {len(all_chunks)} total chunks.", file=sys.stderr)
    return all_chunks

# --- Embedding Creation & Saving (Unchanged) ---
def create_embeddings_and_save(chunks):
    print(f"Creating embeddings with Gemini model: {EMBEDDING_MODEL}...", file=sys.stderr)
    try:
        if not os.getenv('GOOGLE_API_KEY'): raise ValueError("GOOGLE_API_KEY not found in environment for API call.")
        result = genai.embed_content(model=EMBEDDING_MODEL, content=chunks, task_type="RETRIEVAL_DOCUMENT")
        embeddings_np = np.array(result['embedding'])
        np.save(CACHE_EMBEDDINGS_PATH, embeddings_np)
        with open(CACHE_CHUNKS_PATH, 'w', encoding='utf-8') as f: json.dump(chunks, f)
        print(f"Successfully created and saved '{CACHE_EMBEDDINGS_PATH}' and '{CACHE_CHUNKS_PATH}'.", file=sys.stderr); return True
    except Exception as e: print(f"FATAL ERROR while creating embeddings: {e}", file=sys.stderr); raise

# --- LLM Query Processing (Unchanged) ---
def generate_hypothetical_questions(query):
    print(f"Generating hypothetical questions...", file=sys.stderr)
    model = genai.GenerativeModel(LLM_MODEL)
    prompt = f"""Based on the following user query, what are three different, specific questions a claims processor would need to find answers to in an insurance policy document? Focus on identifying key terms, waiting periods, and exceptions. USER QUERY: "{query}" Provide the questions as a numbered list."""
    try:
        response = model.generate_content(prompt)
        questions = [line.strip().split(". ", 1)[1] for line in response.text.strip().split("\n") if ". " in line]
        print(f"Generated questions: {questions}", file=sys.stderr); return questions
    except Exception as e: print(f"Warning: Could not generate hypothetical questions. {e}", file=sys.stderr); return []
def process_query_with_gemini(query, index, chunks):
    print(f"Processing query: '{query}'", file=sys.stderr)
    generated_questions = generate_hypothetical_questions(query); all_queries = [query] + generated_questions
    if not os.getenv('GOOGLE_API_KEY'): raise ValueError("GOOGLE_API_KEY not found for API call.")
    all_embeddings_result = genai.embed_content(model=EMBEDDING_MODEL, content=all_queries, task_type="RETRIEVAL_QUERY")
    all_embeddings = all_embeddings_result['embedding']
    k = 5; retrieved_indices = set()
    for embedding in all_embeddings:
        distances, indices = index.search(np.array([embedding]), k)
        for i in indices[0]: retrieved_indices.add(i)
    retrieved_chunks = [chunks[i] for i in retrieved_indices]
    print(f"--- Retrieved Clauses for Context ({len(retrieved_chunks)} unique chunks) ---", file=sys.stderr)
    for i, chunk in enumerate(retrieved_chunks): print(f"[{i+1}] {chunk}", file=sys.stderr)
    print("-------------------------------------", file=sys.stderr); context_clauses = "\n---\n".join(retrieved_chunks)
    print(f"Step 3: Sending request to Gemini LLM for final decision...", file=sys.stderr)
    prompt = f"""Your primary task is to act as an expert insurance claims processor. Evaluate the user's query based ONLY on the provided policy clauses. Your entire response must be a single, valid JSON object, with no additional text or explanations. [POLICY CLAUSES]: --- {context_clauses} --- [USER QUERY]: "{query}" [INSTRUCTIONS]: 1. Analyze the user's query and the policy clauses. 2. Make a final decision: "Approved" or "Rejected". 3. Provide a clear justification, mapping your reasoning to the specific clauses. 4. If rejected, the amount is 0. If approved, state that the final amount depends on network hospital rates. 5. Use the following JSON format for your response. [JSON_FORMAT]: {{"Decision": "Approved/Rejected", "Amount": "Calculated or descriptive amount", "Justification": [{{ "Reasoning": "...", "SupportingClause": "..." }}]}}"""
    model = genai.GenerativeModel(LLM_MODEL, generation_config={"response_mime_type": "application/json"})
    try:
        response = model.generate_content(prompt); return response.text
    except Exception as e: print(f"Error calling Gemini API: {e}", file=sys.stderr); return json.dumps({"error": f"An error occurred calling the Gemini API: {e}"}, indent=2)

# --- On-the-fly processing for a single file (Unchanged) ---
def process_single_file_and_query_rag(file_path, query):
    print(f"\n--- Starting On-the-Fly Processing for file: {file_path} ---", file=sys.stderr)
    all_chunks = []; filename = os.path.basename(file_path)
    try:
        # Prefer detection by extension, but if missing/unknown, try common formats in order: PDF -> DOCX -> TXT
        full_text = None
        lowered = filename.lower()
        try_order = []
        if lowered.endswith('.pdf'):
            try_order = ['pdf']
        elif lowered.endswith('.docx'):
            try_order = ['docx']
        elif lowered.endswith('.txt'):
            try_order = ['txt']
        else:
            try_order = ['pdf', 'docx', 'txt']

        last_error = None
        for kind in try_order:
            try:
                if kind == 'pdf':
                    full_text = extract_text_from_pdf(file_path)
                elif kind == 'docx':
                    full_text = extract_text_from_docx(file_path)
                elif kind == 'txt':
                    full_text = extract_text_from_txt(file_path)
                if full_text:
                    break
            except Exception as inner_e:
                last_error = inner_e
                continue
        if full_text is None or full_text.strip() == "":
            raise ValueError(f"Could not extract text from file. Last error: {last_error}")
        # Create chunks from extracted text
        chunks = chunk_text(full_text)
        all_chunks.extend(chunks)
        if not all_chunks:
            raise ValueError("Could not extract any text chunks from the document. The document might be empty or image-based.")
        print(f"Successfully partitioned document into {len(all_chunks)} chunks.", file=sys.stderr)
    except Exception as e: print(f"Error during chunking: {e}", file=sys.stderr); raise
    print(f"\nCreating embeddings via Gemini API (this may take a moment)...", file=sys.stderr)
    try:
        if not os.getenv('GOOGLE_API_KEY'): raise ValueError("GOOGLE_API_KEY not found in environment for API call.")
        result = genai.embed_content(model=EMBEDDING_MODEL, content=all_chunks, task_type="RETRIEVAL_DOCUMENT")
        embeddings_np = np.array(result['embedding'])
        index = faiss.IndexFlatL2(embeddings_np.shape[1]); index.add(embeddings_np)
        print("In-memory vector store created successfully.", file=sys.stderr)
    except Exception as e: print(f"FATAL ERROR while creating embeddings: {e}", file=sys.stderr); raise
    print(f"\nProcessing query via Gemini API...", file=sys.stderr)
    final_response = process_query_with_gemini(query, index, all_chunks)
    print("--- On-the-Fly Processing Complete ---", file=sys.stderr); return final_response


# --- Main execution block for direct script calls (e.g., for build_kb or testing) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG operations directly for local build/test.")
    parser.add_argument('--mode', required=True, choices=['build_kb', 'test_prebuilt_kb', 'test_on_the_fly'],
                        help="Operation mode: 'build_kb', 'test_prebuilt_kb', 'test_on_the_fly'.")
    parser.add_argument('--query', type=str, help="The natural language query.")
    parser.add_argument('--file', type=str, help="Path to the document file for on_the_fly mode.")

    args = parser.parse_args()

    # Change CWD to project root for consistent pathing for all file operations
    project_root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root_dir) # This changes the current working directory for the script's execution

    # Load .env for direct execution (e.g., build_kb mode)
    load_dotenv()
    if not os.getenv('GOOGLE_API_KEY'):
        print("FATAL ERROR: GOOGLE_API_KEY not found in .env file for direct script run. Please set it.", file=sys.stderr)
        exit(1)
    
    # Execute the requested mode
    if args.mode == 'build_kb':
        print("Running in BUILD_KB mode...", file=sys.stderr)
        chunks = load_and_chunk_documents()
        if chunks:
            if create_embeddings_and_save(chunks):
                print("KB build successful.", file=sys.stderr)
                exit(0)
            else:
                print("KB build failed.", file=sys.stderr)
                exit(1)
        else:
            print("No chunks to build KB.", file=sys.stderr)
            exit(1)
    
    elif args.mode == 'test_prebuilt_kb':
        print("Running in TEST_PREBUILT_KB mode...", file=sys.stderr)
        if not args.query:
            print("Error: --query is required for test_prebuilt_kb mode.", file=sys.stderr)
            exit(1)
        
        try:
            prebuilt_embeddings = np.load(CACHE_EMBEDDINGS_PATH)
            with open(CACHE_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                prebuilt_chunks = json.load(f)
            prebuilt_index = faiss.IndexFlatL2(prebuilt_embeddings.shape[1])
            prebuilt_index.add(prebuilt_embeddings)
            print("Pre-built KB loaded for query test.", file=sys.stderr)

            result_json = process_query_with_gemini(args.query, prebuilt_index, prebuilt_chunks)
            print(result_json) # Print JSON to stdout
            exit(0)
        except FileNotFoundError:
            print(f"Error: Pre-built KB files not found ({CACHE_EMBEDDINGS_PATH}, {CACHE_CHUNKS_PATH}). Run build_kb mode first.", file=sys.stderr)
            exit(1)
        except Exception as e:
            print(f"Error in test_prebuilt_kb mode: {e}", file=sys.stderr)
            exit(1)

    elif args.mode == 'test_on_the_fly':
        print("Running in TEST_ON_the_fly mode...", file=sys.stderr)
        if not args.query or not args.file:
            print("Error: --query and --file are required for test_on_the_fly mode.", file=sys.stderr)
            exit(1)
        
        try:
            result_json = process_single_file_and_query_rag(args.file, args.query)
            print(result_json) # Print JSON to stdout
            exit(0)
        except Exception as e:
            print(f"Error in test_on_the_fly mode: {e}", file=sys.stderr)
            exit(1)