"""
Script to run the Flight Route Advisor application
First runs the data pipeline, then starts the Streamlit app
"""

import subprocess
import sys
from pathlib import Path
import os


def run_pipeline():
    """Run the data pipeline to prepare data"""
    print("Running data pipeline...")
    
    try:
        # Run the main pipeline
        result = subprocess.run([
            sys.executable, "-m", "pipeline.main_pipeline"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("[OK] Pipeline completed successfully!")
            print(result.stdout)
        else:
            print("[ERROR] Pipeline failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"[ERROR] Error running pipeline: {e}")
        return False
    
    return True


def run_streamlit():
    """Run the Streamlit application"""
    print("Starting Streamlit application...")
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"[ERROR] Error running Streamlit: {e}")


def main():
    """Main function"""
    print("Flight Route Advisor - Starting Application")
    print("=" * 50)
    
    # Check if data exists
    data_dir = Path("data/cleaned")
    required_files = [
        "airports_cleaned.csv",
        "airlines_cleaned.csv",
        "routes_graph.csv"
    ]
    
    data_exists = all((data_dir / file).exists() for file in required_files)
    
    if not data_exists:
        print("Data not found. Please run the notebook first to generate cleaned data.")
        print("Expected files:")
        for file in required_files:
            print(f"  - {file}")
        return
    else:
        print("[OK] Data files found. Starting Streamlit app.")
    
    # Start Streamlit app
    run_streamlit()


if __name__ == "__main__":
    main()
