"""
Validator module for scanning and filtering supported image files.
"""

import itertools
from pathlib import Path
from typing import List, Optional, Tuple

SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.jpe')


def is_supported_image(file_path: Path) -> bool:
    """Check if the given path is a file with a supported image extension (case-insensitive)."""
    return file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def scan_images(
    directory: Path,
    recursive: bool = False,
    limit: Optional[int] = None
) -> Tuple[List[Path], int]:
    """
    Scan image files from the specified directory, sort them ascending (ASC),
    and apply the user-specified limit.
    
    Returns:
        Tuple[List[Path], int]: (files_to_process, total_count_found)
    """
    pattern = "**/*" if recursive else "*"
    # Collect all supported files
    all_files = [
        p for p in directory.glob(pattern)
        if is_supported_image(p)
    ]

    # Sort files ascending (A-Z / 0-9) based on relative path
    all_files.sort(key=lambda p: str(p.relative_to(directory)).lower())

    total_found = len(all_files)

    if limit is not None and limit > 0:
        files_to_process = all_files[:limit]
    else:
        files_to_process = all_files

    return files_to_process, total_found

