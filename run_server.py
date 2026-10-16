"""Standalone server runner with full error output."""
import sys, os
sys.path.insert(0, r'C:\Users\dhruv\kiro-memory')
os.environ.setdefault('WORKSPACE_PATH', r'C:\Users\dhruv\kiro-memory')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import uvicorn
from src.api.app import create_app

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8765, log_level='debug')
