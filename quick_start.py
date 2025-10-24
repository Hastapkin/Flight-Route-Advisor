"""
Quick start script for Flight Route Advisor
Automated setup and launch
"""

import subprocess
import sys
from pathlib import Path
import os


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def setup_environment():
    """Setup virtual environment and install dependencies"""
    print("🚀 Setting up Flight Route Advisor...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            return False
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_script = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    print("✅ Environment setup completed")
    return True


def run_pipeline():
    """Run the data pipeline"""
    print("📊 Running data pipeline...")
    
    # Determine Python executable
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    if not run_command(f"{python_cmd} -m pipeline.main_pipeline", "Processing flight data"):
        print("⚠️ Pipeline failed, but continuing...")
        return False
    
    return True


def run_application():
    """Run the Streamlit application"""
    print("🌐 Starting web application...")
    
    # Determine Python executable
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    print("🚀 Launching Streamlit application...")
    print("📱 The app will open in your browser at: http://localhost:8501")
    print("⏹️ Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([python_cmd, "-m", "streamlit", "run", "app/streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return False
    
    return True


def main():
    """Main quick start function"""
    print("=" * 60)
    print("✈️ FLIGHT ROUTE ADVISOR - QUICK START")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the project root directory")
        return
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed. Please check the errors above.")
        return
    
    # Run pipeline
    run_pipeline()
    
    # Ask user if they want to run the app
    print("\n" + "=" * 60)
    response = input("🚀 Do you want to start the web application now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes', '']:
        run_application()
    else:
        print("\n📝 To start the application later, run:")
        print("   python run_app.py")
        print("   or")
        print("   streamlit run app/streamlit_app.py")
    
    print("\n✅ Quick start completed!")


if __name__ == "__main__":
    main()
