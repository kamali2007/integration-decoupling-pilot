import uvicorn
import os
import sys
from pathlib import Path

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting Integration Control Tower Backend on http://{host}:{port}")
    print(f"Interactive API Docs available at http://{host}:{port}/docs")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
