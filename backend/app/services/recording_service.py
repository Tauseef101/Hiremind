"""
recording_service.py – saves interview video recordings uploaded from the browser.

Recordings are stored at RECORDING_DIR (set in .env) under:
    <RECORDING_DIR>/application_<aid>/<timestamp>_<candidate_name>.<ext>
"""
import logging
import uuid
from datetime import datetime
from pathlib import Path
from ..config import RECORDING_DIR

logger = logging.getLogger(__name__)


def save_recording(data: bytes, filename: str, application_id: int, candidate_name: str) -> Path:
    """
    Persist a video blob to disk and return the saved Path.

    :param data:             Raw bytes of the video file
    :param filename:         Original filename (used for extension detection)
    :param application_id:  Application ID – used to group recordings
    :param candidate_name:  Candidate name – embedded in the saved filename
    :return:                 Absolute Path of the saved file
    :raises ValueError:      If the extension is not in the allowed list
    """
    ext = Path(filename).suffix.lower()
    allowed = {".webm", ".mp4", ".ogg", ".mkv", ".mov"}
    if ext not in allowed:
        raise ValueError(f"Unsupported recording format '{ext}'. Allowed: {', '.join(sorted(allowed))}")

    # Create a per-application subfolder
    folder = RECORDING_DIR / f"application_{application_id}"
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() else "_" for c in candidate_name)
    unique = uuid.uuid4().hex[:6]
    save_path = folder / f"{timestamp}_{safe_name}_{unique}{ext}"

    save_path.write_bytes(data)
    logger.info("Recording saved: %s (%d bytes)", save_path, len(data))
    return save_path


def list_recordings(application_id: int) -> list[dict]:
    """
    Return metadata for all recordings for a given application.

    :param application_id: Application ID
    :return:               List of dicts with 'filename', 'path', 'size_mb', 'created_at'
    """
    folder = RECORDING_DIR / f"application_{application_id}"
    if not folder.exists():
        return []
    results = []
    for f in sorted(folder.iterdir()):
        if f.is_file():
            stat = f.stat()
            results.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / 1_048_576, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
    return results
