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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_startup.log')
    ]
)

def cleanup_system():
    """Clean up any existing processes and locked files"""
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'wildrandom.db'
    
    # Kill any Python processes running our application
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any('wildrandom' in str(cmd).lower() for cmd in cmdline):
                    if proc.pid != os.getpid():  # Don't kill ourselves
                        logging.info(f"Terminating process {proc.pid}")
                        proc.terminate()
                        proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

    # Wait a moment for processes to terminate
    time.sleep(2)
    
    # Only try to close any open database connections
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            logging.info(f"Closed any open connections to database: {db_path}")
        except Exception as e:
            logging.warning(f"Error managing database connections: {e}")

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def start_flask_app():
    """Start the Flask application"""
    try:
        # Set up environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        env['APP_PORT'] = '5001'  # Changed from FLASK_RUN_PORT
        env['FLASK_RUN_HOST'] = '0.0.0.0'

        # Start the Flask application
        cmd = [sys.executable, '-c', 
               'from app import run_app; run_app(port=5001)']
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for the application to start
        time.sleep(2)
        
        if process.poll() is None:
            logging.info("Flask application started successfully on port 5001")
            return process
        else:
            stdout, stderr = process.communicate()
            logging.error(f"Flask application failed to start: {stderr.decode()}")
            return None

    except Exception as e:
        logging.error(f"Error starting Flask application: {str(e)}")
        return None

def initialize_database():
    """Initialize or reset the database"""
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/create_db.py'],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("Database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Database initialization failed: {e.stderr}")
        return False

def main():
    # Set up project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean up any existing processes
    cleanup_system()
    
    # Create data directory if it doesn't exist
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Initialize database only if it doesn't exist
    db_path = data_dir / 'wildrandom.db'
    if not db_path.exists():
        if not initialize_database():
            return
    
    # Start Flask application
    app_process = start_flask_app()
    
    if not app_process:
        logging.error("Failed to start the application")
        return

    logging.info("System started successfully")
    logging.info("Press Ctrl+C to shutdown")

    try:
        while True:
            if app_process.poll() is not None:
                logging.error("Flask application has stopped unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        app_process.terminate()
        try:
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_process.kill()
        logging.info("System shutdown complete")

if __name__ == "__main__":
    main()