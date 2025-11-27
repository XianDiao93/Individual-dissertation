import subprocess
import webbrowser
import time
import sys
import signal
from pathlib import Path


def main():
    # ==== Paths relative to this script ====
    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir / "backend"
    frontend_index = base_dir / "frontend" / "src" / "index.html"

    if not backend_dir.exists():
        print(f"[ERROR] Backend directory not found: {backend_dir}")
        return

    if not frontend_index.exists():
        print(f"[ERROR] Frontend index.html not found: {frontend_index}")
        return

    # ==== Start backend (FastAPI with uvicorn) ====
    # Use current Python interpreter: sys.executable
    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]

    print("====================================")
    print(" Starting backend server (FastAPI) ")
    print("====================================")
    print("Working directory:", backend_dir)
    print("Command:", " ".join(uvicorn_cmd))
    print()

    try:
        backend_proc = subprocess.Popen(
            uvicorn_cmd,
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        print("[ERROR] Failed to start uvicorn.")
        print("Make sure uvicorn is installed in this Python environment:")
        print(f"  {sys.executable} -m pip install uvicorn fastapi")
        return

    # ==== Give the server a moment to start ====
    time.sleep(1.5)

    # ==== Open frontend in default browser ====
    print("====================================")
    print(" Opening frontend UI in browser     ")
    print("====================================")
    print("Frontend file:", frontend_index)
    print()

    webbrowser.open(frontend_index.as_uri())

    print("------------------------------------")
    print("Backend running at: http://127.0.0.1:8000")
    print("Frontend opened from:", frontend_index)
    print("------------------------------------")
    print("Press ENTER to stop the backend server and exit.")
    print("(Or press Ctrl+C)")
    print()

    try:
        # Keep printing backend logs in background (optional)
        # If you don't want logs here, you can remove this loop and just do input()
        while True:
            # Non-blocking check if backend is still alive
            if backend_proc.poll() is not None:
                print("\n[INFO] Backend process has exited.")
                break

            # Check user input without blocking logs
            # Simplest: just blocking input; logs will stop until you press enter.
            # For simplicity in a student project, we just use input().
            input()
            print("[INFO] Stop requested by user.")
            break

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received, shutting down...")

    finally:
        # ==== Gracefully stop backend ====
        if backend_proc.poll() is None:
            print("[INFO] Terminating backend server...")
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[WARN] Backend did not exit in time. Killing it...")
                backend_proc.kill()

        print("[INFO] Backend server stopped. Bye.")


if __name__ == "__main__":
    main()
