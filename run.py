import os
import subprocess
import sys
import time
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_backend():
    """Run the FastAPI backend server"""
    print("Starting backend API server...")
    api_process = subprocess.Popen(
        ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Give the server a moment to start
    return api_process

def run_frontend():
    """Run the Streamlit frontend"""
    print("Starting Streamlit UI...")
    ui_process = subprocess.Popen(
        ["streamlit", "run", "src/ui/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Give the server a moment to start
    return ui_process

def main():
    """Main function to run both backend and frontend"""
    # Run backend
    api_process = run_backend()
    print("Backend API running at http://localhost:8000")
    
    # Run frontend
    ui_process = run_frontend()
    print("Streamlit UI running. Check the console output for the URL.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        api_process.terminate()
        ui_process.terminate()
        print("Servers shut down successfully.")

if __name__ == "__main__":
    main()
