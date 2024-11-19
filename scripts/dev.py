# scripts/dev.py

import subprocess
import sys
import os
from threading import Thread
import signal
import psutil
import time

def kill_process_by_port(port):
    """Kill process using specific port"""
    try:
        # Windows specific command
        result = subprocess.run(f'netstat -ano | findstr :{port}', shell=True, capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if f':{port}' in line:
                pid = line.strip().split()[-1]
                try:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                except:
                    pass
    except:
        pass

def cleanup():
    """Clean up all related processes"""
    print("Cleaning up processes...")
    
    # Kill processes on common ports
    kill_process_by_port(5001)  # Flask
    for port in range(5175, 5185):  # Vite ports
        kill_process_by_port(port)
    
    # Kill by process name
    process_names = ['node.exe', 'python.exe']
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] in process_names:
                cmdline = proc.info['cmdline']
                if cmdline and any(x in str(cmdline).lower() for x in ['vite', 'flask', 'wildrandom']):
                    proc.kill()
        except:
            pass
    
    time.sleep(2)  # Wait for processes to clean up
    print("Cleanup completed")

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    print("\nReceived shutdown signal...")
    cleanup()
    print("Exiting...")
    sys.exit(0)

def run_frontend():
    # Store original directory
    original_dir = os.getcwd()
    
    try:
        # Change to frontend directory for npm command
        frontend_dir = os.path.join(original_dir, 'frontend')
        os.chdir(frontend_dir)
        
        if sys.platform == 'win32':
            subprocess.run('npm run dev', shell=True)
        else:
            subprocess.run(['npm', 'run', 'dev'])
    finally:
        # Restore original directory
        os.chdir(original_dir)

def run_backend():
    # Get absolute path to start_system.py
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    start_script = os.path.join(project_root, 'scripts', 'start_system.py')
    
    if sys.platform == 'win32':
        subprocess.run(f'python {start_script}', shell=True)
    else:
        subprocess.run(['python', start_script])

if __name__ == '__main__':
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure we start in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # First, clean up any existing processes
    cleanup()
    
    # Start frontend in a separate thread
    frontend_thread = Thread(target=run_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # Run backend in main thread (will keep script running)
    run_backend()