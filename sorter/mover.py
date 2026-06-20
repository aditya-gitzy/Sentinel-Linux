import os
import shutil
import logging
import time
from pathlib import Path

def is_file_ready(file_path: str, wait_time: int) -> bool:
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(wait_time)
        return initial_size == os.path.getsize(file_path)
    except OSError:
        # File is likely locked by Windows (still downloading or open in another app)
        return False

def safe_move(source: Path, destination_dir: Path):
    try:
        if not destination_dir.exists():
            destination_dir.mkdir(parents=True, exist_ok=True)

        target_path = destination_dir / source.name
        
        counter = 1
        while target_path.exists():
            target_path = destination_dir / f"{source.stem}_{counter}{source.suffix}"
            counter += 1

        shutil.move(str(source), str(target_path))
        logging.info(f"Successfully moved: {source.name} -> {target_path}")
    except Exception as e:
        logging.error(f"Failed to move {source.name}: {e}")