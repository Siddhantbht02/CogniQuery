import os
from dotenv import load_dotenv

# ==============================================================================
#  CRITICAL FIX: Load environment variables from .env file FIRST.
# ==============================================================================
print("Loading environment variables from .env file...")
load_dotenv()
# ==============================================================================

# Now that the environment is loaded, we can safely import our logic module,
# which will successfully find the GOOGLE_API_KEY when it runs its top-level code.
from logic import load_and_chunk_document, create_embeddings_and_save

# --- Main execution block ---
if __name__ == "__main__":
    # We can add a more robust check here now.
    if not os.getenv('GOOGLE_API_KEY'):
        print("FATAL ERROR: GOOGLE_API_KEY was not found after loading .env file.")
        print("Please ensure your .env file is in the root directory and contains the correct key.")
    else:
        print("GOOGLE_API_KEY loaded successfully.")
        print("Starting knowledge base build process...")
        
        chunks = load_and_chunk_document()
        if chunks:
            # The logic module is now correctly configured with the API key
            create_embeddings_and_save(chunks)
        
        print("Build process complete.")