# backend/app/utils/file_utils.py
from pathlib import Path
import datetime


# Project root = ".../Individual dissertation"
# Navigate 3 levels up to locate project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Global output directory for generated files (PDFs, images, etc.)
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_output_dir() -> Path:
    """
    Return the output directory (ensure it exists).
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def make_timestamped_filename(prefix: str, suffix: str = ".pdf") -> str:
    """
    Generate a timestamped filename, e.g.:
    contract_20251130_143512.pdf
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}{suffix}"


def save_bytes_to_output(content: bytes, prefix: str, suffix: str = ".pdf") -> Path:
    """
    Save raw bytes to the output directory (commonly used for PDFs).
    """
    out_dir = get_output_dir()
    filename = make_timestamped_filename(prefix, suffix)
    path = out_dir / filename

    path.write_bytes(content)
    return path


def save_upload_to_output(upload_file, prefix: str) -> Path:
    """
    Generate a file path for an uploaded file (does NOT write the file).

    Note:
    - This function only returns the destination path.
    - The caller must handle writing, e.g.:
        content = await upload_file.read()
        path.write_bytes(content)
    """
    out_dir = get_output_dir()

    # Preserve original file extension if available
    suffix = Path(upload_file.filename).suffix or ""

    filename = make_timestamped_filename(prefix, suffix or ".bin")
    path = out_dir / filename

    return path