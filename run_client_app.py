"""
Run Client-Side Flight Route Advisor Application
Modern, visual interface for end users
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "app" / "client_app.py"
    
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8502",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    print("Starting Flight Route Advisor - Client Application...")
    print("Open your browser to: http://localhost:8502")
    print("Press Ctrl+C to stop the server")
    
    subprocess.run(cmd)

