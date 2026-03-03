import subprocess
import sys
import os
from pathlib import Path
from app.config import OPENAI_API_KEY

def main():
    backend_dir = Path(__file__).resolve().parent
    print("Working directory:", backend_dir)

    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
    ]
    print("Command:", " ".join(cmd))
    print("Starting backend server (Ctrl+C to stop)...")
    print()


    subprocess.run(cmd, cwd=str(backend_dir))

    print()
    print("Backend server stopped.")

if __name__ == "__main__":
    main()
