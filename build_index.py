import os
from dotenv import load_dotenv

# Load environment variables from .env file first
print("Loading environment variables...")
load_dotenv()

# Import the logic functions after the environment is set up
from logic import load_and_chunk_documents, create_embeddings_and_save

# --- Main execution block ---
if __name__ == "__main__":
    if not os.getenv('GOOGLE_API_KEY'):
        print("FATAL ERROR: GOOGLE_API_KEY was not found.")
    else:
        print("GOOGLE_API_KEY loaded successfully.")
        print("Starting knowledge base build process from 'source_documents' folder...")
        
        # Call the new, more powerful function
        chunks = load_and_chunk_documents()
        
        if chunks:
            # The rest of the process is the same
            create_embeddings_and_save(chunks)
        else:
            print("No chunks were created. Please check the 'source_documents' folder.")
        
        print("Build process complete.")