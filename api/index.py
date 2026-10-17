import os
import sys

# Ensure root directory is in sys.path for Vercel serverless function execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

