import numpy as np
import faiss
import google.generativeai as genai
import json
import os
import fitz  # PyMuPDF
import docx  # python-docx

# --- Configuration ---
# (This part is unchanged)
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
except (ValueError, Exception) as e:
    print(f"Warning: Could not configure Gemini API. Error: {e}")

# --- Model and File Paths ---
EMBEDDING_MODEL = 'models/text-embedding-004'
LLM_MODEL = "gemini-2.5-pro"
SOURCE_DOCS_PATH = "source_documents" 
CACHE_EMBEDDINGS_PATH = "knowledge_base.npy"
CACHE_CHUNKS_PATH = "knowledge_base_chunks.json"

# --- Document Processing and Chunking (UPDATED) ---

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """
    Splits a long text into smaller chunks of a specified size with overlap.
    This is a simplified recursive text splitter.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path):
    """Extracts text from a plain text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_and_chunk_documents():
    """
    Loads documents, extracts text, and then uses a smarter chunking strategy.
    """
    print(f"Loading documents from directory: {SOURCE_DOCS_PATH}")
    all_chunks = []
    
    if not os.path.exists(SOURCE_DOCS_PATH):
        print(f"Error: Directory not found at '{SOURCE_DOCS_PATH}'")
        return all_chunks

    for filename in os.listdir(SOURCE_DOCS_PATH):
        file_path = os.path.join(SOURCE_DOCS_PATH, filename)
        if not os.path.isfile(file_path):
            continue

        print(f"--> Processing file: {filename}")
        full_text = ""
        try:
            if filename.lower().endswith('.pdf'):
                full_text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith('.docx'):
                full_text = extract_text_from_docx(file_path)
            elif filename.lower().endswith('.txt'):
                full_text = extract_text_from_txt(file_path)
            else:
                print(f"    Unsupported file type: {filename}")
                continue
            
            # --- THE CRITICAL CHANGE IS HERE ---
            # Instead of a simple split, we use our new chunking function.
            chunks = chunk_text(full_text)
            all_chunks.extend(chunks)
            print(f"    Extracted and split into {len(chunks)} chunks.")
            
        except Exception as e:
            print(f"    Error processing file {filename}: {e}")
            
    print(f"Successfully processed all files into {len(all_chunks)} total chunks.")
    return all_chunks


# --- The rest of the file (create_embeddings_and_save, process_query_with_gemini) is UNCHANGED ---

def create_embeddings_and_save(chunks):
    # (This function is identical to before)
    print(f"Creating embeddings with Gemini model: {EMBEDDING_MODEL}...")
    try:
        result = genai.embed_content(model=EMBEDDING_MODEL, content=chunks, task_type="RETRIEVAL_DOCUMENT")
        embeddings_np = np.array(result['embedding'])
        np.save(CACHE_EMBEDDINGS_PATH, embeddings_np)
        with open(CACHE_CHUNKS_PATH, 'w', encoding='utf-8') as f: json.dump(chunks, f)
        print(f"Successfully created and saved '{CACHE_EMBEDDINGS_PATH}' and '{CACHE_CHUNKS_PATH}'.")
        return True
    except Exception as e:
        print(f"FATAL ERROR while creating embeddings: {e}")
        return False

# ... (all the code above this function remains the same) ...

def generate_hypothetical_questions(query):
    """Uses the LLM to generate follow-up questions to improve retrieval."""
    # Note: We don't need JSON mode for this simple generation task.
    model = genai.GenerativeModel(LLM_MODEL)
    
    prompt = f"""
Based on the following user query, what are three different, specific questions a claims processor would need to find answers to in an insurance policy document?
Focus on identifying key terms, waiting periods, and exceptions.

USER QUERY: "{query}"

Provide the questions as a numbered list.
"""
    
    try:
        response = model.generate_content(prompt)
        # Clean up the output to get a list of questions
        questions = [line.strip().split(". ", 1)[1] for line in response.text.strip().split("\n") if ". " in line]
        print(f"    Generated hypothetical questions for retrieval: {questions}")
        return questions
    except Exception as e:
        print(f"    Warning: Could not generate hypothetical questions. {e}")
        return []

def process_query_with_gemini(query, index, chunks):
    """The main RAG processing function, now with Multi-Query Retrieval."""
    print(f"Processing query: '{query}'")
    
    # --- STEP 1: MULTI-QUERY RETRIEVAL ---
    # Generate hypothetical questions
    generated_questions = generate_hypothetical_questions(query)
    
    # Combine the original query with the generated ones
    all_queries = [query] + generated_questions
    
    # Embed all queries at once (more efficient)
    all_embeddings_result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=all_queries,
        task_type="RETRIEVAL_QUERY"
    )
    all_embeddings = all_embeddings_result['embedding']
    
    # Perform a search for each embedding and collect the unique results
    k = 3 # Retrieve top 3 chunks for EACH question
    retrieved_indices = set()
    for embedding in all_embeddings:
        distances, indices = index.search(np.array([embedding]), k)
        for i in indices[0]:
            retrieved_indices.add(i)
    
    retrieved_chunks = [chunks[i] for i in retrieved_indices]
    print(f"    Retrieved {len(retrieved_chunks)} unique chunks from multi-query search.")
    
    # --- STEP 2: GENERATION (REASONING) ---
    # The rest of the function is the same, but now it has better context.
    context_clauses = "\n---\n".join(retrieved_chunks)
    
    prompt = f"""
Your primary task is to act as an expert insurance claims processor.
Evaluate the user's query based ONLY on the provided policy clauses.
Your entire response must be a single, valid JSON object, with no additional text or explanations.

[POLICY CLAUSES]:
---
{context_clauses}
---

[USER QUERY]:
"{query}"

[INSTRUCTIONS]:
1. Analyze the user's query and the policy clauses.
2. Make a final decision: "Approved" or "Rejected".
3. Provide a clear justification, mapping your reasoning to the specific clauses.
4. If rejected, the amount is 0. If approved, state that the final amount depends on network hospital rates.
5. Use the following JSON format for your response.

[JSON_FORMAT]:
{{
  "Decision": "...",
  "Amount": "...",
  "Justification": [{{ "Reasoning": "...", "SupportingClause": "..." }}]
}}
"""
    
    model = genai.GenerativeModel(LLM_MODEL, generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(prompt)
    return response.text
# ... (all your existing functions like load_and_chunk_documents, process_query_with_gemini, etc., stay the same) ...

# --- NEW FUNCTION FOR ON-THE-FLY PROCESSING ---

# --- This is the new, more robust version of the function ---

def process_single_file_and_query(file_path, query):
    """
    Performs the entire RAG pipeline for a single uploaded file with detailed logging.
    """
    print(f"\n--- Starting On-the-Fly Processing ---")
    print(f"File: {file_path}")
    print(f"Query: {query}")

    # 1. Load and Chunk the single document
    print("\n[Step 1/3] Partitioning document into chunks...")
    all_chunks = []
    filename = os.path.basename(file_path)
    try:
        if filename.lower().endswith('.pdf'):
            full_text = extract_text_from_pdf(file_path)
            chunks = chunk_text(full_text)
            all_chunks.extend(chunks)
        elif filename.lower().endswith('.docx'):
            full_text = extract_text_from_docx(file_path)
            chunks = chunk_text(full_text)
            all_chunks.extend(chunks)
        elif filename.lower().endswith('.txt'):
            full_text = extract_text_from_txt(file_path)
            chunks = chunk_text(full_text)
            all_chunks.extend(chunks)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        if not all_chunks:
            raise ValueError("Could not extract any text chunks from the document. The document might be empty or image-based.")
            
        print(f"Successfully partitioned document into {len(all_chunks)} chunks.")

    except Exception as e:
        print(f"Error during chunking: {e}")
        # Re-raise the exception to ensure the server returns a 500 error
        raise

    # 2. Create Embeddings and build an IN-MEMORY vector store
    print("\n[Step 2/3] Creating embeddings via Gemini API (this may take a moment)...")
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=all_chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings_np = np.array(result['embedding'])
        
        index = faiss.IndexFlatL2(embeddings_np.shape[1])
        index.add(embeddings_np)
        print("In-memory vector store created successfully.")
    except Exception as e:
        print(f"FATAL ERROR while creating embeddings: {e}")
        raise

    # 3. Process the query against the new, temporary knowledge base
    print("\n[Step 3/3] Processing query via Gemini API...")
    # This calls your other function to do the final reasoning step
    final_response = process_query_with_gemini(query, index, all_chunks)
    print("--- On-the-Fly Processing Complete ---")
    
    return final_response