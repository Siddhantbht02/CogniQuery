# This script is the dedicated entry point for running the server locally.

from dotenv import load_dotenv

# Step 1: Load environment variables from the .env file.
# This MUST be done before importing the Flask app from api.index.
print("Loading environment variables for local development...")
load_dotenv()
print("Environment variables loaded.")

# Step 2: Import the 'app' object from your api/index.py file.
# Because this script is in the root, Python can now correctly find 'api'
# as a module and 'logic' as a sibling module.
from api.index import app

# Step 3: Run the Flask development server.
# The __name__ == '__main__' block ensures this code only runs
# when you execute "python run_local.py".
if __name__ == '__main__':
    print("Starting Flask development server...")
    # The debug=True flag provides helpful error messages.
    app.run(debug=True, port=5000)