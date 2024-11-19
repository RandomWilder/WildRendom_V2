# scripts/start_system.py

import os
import sys
from pathlib import Path
import subprocess
import time
import signal
import psutil
import logging
from datetime import datetime
import socket
import sqlite3

# Fix path resolution
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))  # Add project root to Python path
os.chdir(project_root)  # Change working directory to project root

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_startup.log')
    ]
)

logger = logging.getLogger(__name__)

def cleanup_system():
    """Clean up any existing processes and locked files"""
    db_path = project_root / 'data' / 'wildrandom.db'
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('wildrandom' in str(cmd).lower() for cmd in cmdline):
                    if proc.pid != os.getpid():
                        logging.info(f"Terminating process {proc.pid}")
                        proc.terminate()
                        proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

    time.sleep(2)
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            logging.info(f"Closed any open connections to database: {db_path}")
        except Exception as e:
            logging.warning(f"Error managing database connections: {e}")

def run_app():
    """Run Flask application"""
    try:
        # Import here after path is set up
        from app import create_app
        
        app = create_app()
        logger.info("Created Flask application successfully")
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())  # Print full traceback
        return False
    return True

def main():
    # Create data directory if it doesn't exist
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Clean up any existing processes
    cleanup_system()
    
    # Set environment variables
    os.environ['FLASK_APP'] = str(project_root / 'app.py')
    os.environ['FLASK_ENV'] = 'development'
    os.environ['APP_PORT'] = '5001'
    
    logger.info(f"Starting Flask application from {project_root}")
    run_app()

if __name__ == "__main__":
    main()