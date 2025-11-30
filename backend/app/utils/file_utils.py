# backend/app/utils/file_utils.py
from pathlib import Path
import datetime


# Project root = ".../Individual dissertation"
# file_utils.py 在 backend/app/utils/ 下，所以 parents[3] = project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Global output directory for generated documents
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_output_dir() -> Path:
    """
    Return the global output directory for generated files.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def make_timestamped_filename(prefix: str, suffix: str = ".pdf") -> str:
    """
    Build a simple timestamped filename like:
      contract_20251130_143512.pdf
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}{suffix}"


def save_bytes_to_output(content: bytes, prefix: str, suffix: str = ".pdf") -> Path:
    """
    Save raw bytes to the output directory and return the Path.
    """
    out_dir = get_output_dir()
    filename = make_timestamped_filename(prefix, suffix)
    path = out_dir / filename
    path.write_bytes(content)
    return path


def save_upload_to_output(upload_file, prefix: str) -> Path:
    """
    Save an UploadFile (FastAPI) into the output directory and return the path.
    Useful for keeping product images used in manuals.

    NOTE: this is a synchronous helper; router needs `await upload_file.read()`.
    """
    out_dir = get_output_dir()
    suffix = Path(upload_file.filename).suffix or ""
    filename = make_timestamped_filename(prefix, suffix or ".bin")
    path = out_dir / filename
    # The router will write bytes into this path.
    return path
