# backend/admin/kb_editor.py
"""
Utilities for the KB file editor: directory tree construction and path safety.

All file paths are resolved relative to the KB root directory
(``settings.resolved_kb_path``). Path traversal attempts are rejected.
Only ``.json`` and ``.csv`` files are allowed for editing.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from config import settings

logger = logging.getLogger("aiktc.admin.kb_editor")

# Allowed file extensions for editing
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".json", ".csv"})


def _kb_root() -> Path:
    """Return the resolved KB root directory."""
    return settings.resolved_kb_path.resolve()


def is_safe_path(relative_path: str) -> bool:
    """Check that a relative path contains no traversal sequences or absolute components."""
    if not relative_path:
        return False
    if ".." in relative_path:
        return False
    if os.path.isabs(relative_path):
        return False
    return True


def is_allowed_extension(relative_path: str) -> bool:
    """Check that the file has an allowed extension (.json or .csv)."""
    return Path(relative_path).suffix.lower() in ALLOWED_EXTENSIONS


def get_full_path(relative_path: str) -> Path:
    """Resolve a relative path against the KB root, raising ValueError if it escapes.

    Parameters
    ----------
    relative_path : str
        A forward-slash separated path relative to the KB root
        (e.g. ``"engineering/departments/computer.json"``).

    Returns
    -------
    Path
        Absolute resolved path guaranteed to be inside the KB root.

    Raises
    ------
    ValueError
        If the resolved path is outside the KB root.
    """
    if not is_safe_path(relative_path):
        raise ValueError(f"Unsafe path: {relative_path}")

    root = _kb_root()
    safe = relative_path.lstrip("/").replace("\\", "/")
    full = (root / safe).resolve()

    if not str(full).startswith(str(root)):
        raise ValueError(f"Path escapes KB root: {relative_path}")

    return full


def build_tree() -> list[dict]:
    """Walk the KB directory and return a nested JSON-serialisable tree.

    Each node is a dict with:
      - ``name``     : file/directory basename
      - ``path``     : forward-slash relative path from KB root
      - ``type``     : ``"file"`` or ``"dir"``
      - ``size``     : file size in bytes (files only)
      - ``children`` : list of child nodes (directories only)

    Directories are sorted first, then files, both alphabetically.
    """
    root = _kb_root()
    if not root.is_dir():
        logger.warning(f"KB root does not exist: {root}")
        return []

    result: list[dict] = []
    _walk(root, root, result)
    return result


def _walk(base: Path, current: Path, result: list[dict]) -> None:
    """Recursively populate *result* with tree nodes."""
    try:
        entries = sorted(
            current.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower()),
        )
    except PermissionError:
        logger.warning(f"Permission denied: {current}")
        return

    for entry in entries:
        # Skip hidden files, __pycache__, etc.
        if entry.name.startswith(".") or entry.name == "__pycache__":
            continue

        rel = str(entry.relative_to(base)).replace("\\", "/")

        if entry.is_dir():
            node: dict = {
                "name": entry.name,
                "path": rel,
                "type": "dir",
                "children": [],
            }
            _walk(base, entry, node["children"])
            result.append(node)
        elif entry.suffix.lower() in ALLOWED_EXTENSIONS:
            result.append({
                "name": entry.name,
                "path": rel,
                "type": "file",
                "size": entry.stat().st_size,
            })


def read_file(relative_path: str) -> dict:
    """Read a single KB file and return its metadata + content.

    Returns
    -------
    dict
        ``{"path", "content", "size", "last_modified"}``

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the path is unsafe or has a disallowed extension.
    """
    if not is_allowed_extension(relative_path):
        raise ValueError(f"File type not allowed: {relative_path}")

    full = get_full_path(relative_path)
    if not full.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")

    stat = full.stat()
    content = full.read_text(encoding="utf-8")
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    return {
        "path": relative_path,
        "content": content,
        "size": stat.st_size,
        "last_modified": modified,
    }


def write_file(relative_path: str, content: str) -> Path:
    """Write content to a KB file atomically (temp file + os.replace).

    Parameters
    ----------
    relative_path : str
        Forward-slash relative path (e.g. ``"engineering/overview.json"``).
    content : str
        The full file content to write.

    Returns
    -------
    Path
        The absolute path of the written file.

    Raises
    ------
    ValueError
        If the path is unsafe or has a disallowed extension.
    """
    if not is_allowed_extension(relative_path):
        raise ValueError(f"File type not allowed: {relative_path}")

    full = get_full_path(relative_path)

    # Ensure parent directory exists
    full.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to a temporary file, then replace
    tmp = full.with_suffix(full.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(str(tmp), str(full))
    except Exception:
        # Clean up temp file on failure
        if tmp.exists():
            tmp.unlink()
        raise

    logger.info(f"KB file written: {relative_path} ({len(content)} chars)")
    return full


def safe_delete(relative_path: str) -> None:
    """Delete a file or an empty directory.
    
    Raises
    ------
    ValueError
        If the path is unsafe or escaping root.
    FileNotFoundError
        If the path doesn't exist.
    OSError
        If the directory is not empty or permission is denied.
    """
    full = get_full_path(relative_path)
    
    if not full.exists():
        raise FileNotFoundError(f"Path not found: {relative_path}")
        
    if full.is_file():
        full.unlink()
        logger.info(f"Deleted file: {relative_path}")
    elif full.is_dir():
        # rmdir will raise OSError if not empty
        full.rmdir()
        logger.info(f"Deleted empty directory: {relative_path}")
    else:
        raise ValueError(f"Not a file or directory: {relative_path}")


def safe_create_folder(parent_relative_path: str, folder_name: str) -> Path:
    """Create a new folder inside the specified parent directory.
    
    Raises
    ------
    ValueError
        If the path is unsafe, escaping root, or folder_name contains slashes.
    FileExistsError
        If the folder already exists.
    """
    if "/" in folder_name or "\\" in folder_name or not folder_name.strip():
        raise ValueError("Invalid folder name")
        
    parent_full = get_full_path(parent_relative_path)
    if not parent_full.is_dir():
        raise ValueError(f"Parent path is not a directory: {parent_relative_path}")
        
    relative_new = f"{parent_relative_path.strip('/')}/{folder_name}" if parent_relative_path.strip('/') else folder_name
    new_full = get_full_path(relative_new)
    
    new_full.mkdir(parents=False, exist_ok=False)
    logger.info(f"Created new folder: {relative_new}")
    
    return new_full
