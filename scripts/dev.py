# scripts/dev.py

import subprocess
import sys
import os
from threading import Thread

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
    # Ensure we start in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Start frontend in a separate thread
    frontend_thread = Thread(target=run_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # Run backend in main thread (will keep script running)
    run_backend()