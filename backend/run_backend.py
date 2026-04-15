import subprocess
import sys
import os
from pathlib import Path
from app.config import OPENAI_API_KEY


def main():
    """
    Entry point for starting the backend development server.
    """
    # Resolve backend working directory
    backend_dir = Path(__file__).resolve().parent
    print("Working directory:", backend_dir)

    # Ensure OpenAI API key is available to the subprocess
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    # Uvicorn command to launch FastAPI app
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

    # Run the server as a subprocess
    subprocess.run(cmd, cwd=str(backend_dir))

    print()
    print("Backend server stopped.")


if __name__ == "__main__":
    main()