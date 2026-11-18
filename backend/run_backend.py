# backend/run_backend.py
import os
import sys
from pathlib import Path
import uvicorn

if __name__ == "__main__":
    backend_dir = Path(__file__).parent.resolve()
    os.chdir(backend_dir)
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    print(f"Starting AIKTC Chatbot FastAPI Backend on http://localhost:8001 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info")
