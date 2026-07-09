"""Safe workspace path management for the Agnes media router plugin."""

from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration — override via environment variables at import time
# ---------------------------------------------------------------------------
_DEFAULT_ROOT = Path.home() / "workspace"
WORKSPACE_ROOT = Path(
    os.getenv("AGNES_WORKSPACE_ROOT", str(_DEFAULT_ROOT))
).expanduser().resolve()
ALLOWED_SUBDIRS = {"images", "videos"}


def get_and_validate_project_path(project_name: str, sub_dir: str = "") -> Path:
    """Return a safe project/subdirectory path inside WORKSPACE_ROOT.

    Parameters
    ----------
    project_name : str
        A single-directory slug. Must not contain path separators, "..",
        absolute paths, or non-ASCII characters.
    sub_dir : str
        One of the allowed subdirectories (images, videos).

    Returns
    -------
    pathlib.Path
        Resolved absolute path, guaranteed to be under WORKSPACE_ROOT.

    Raises
    ------
    ValueError
        If project_name or sub_dir is invalid.
    PermissionError
        If the resolved path escapes WORKSPACE_ROOT.
    """
    if not isinstance(project_name, str):
        raise ValueError("project_name must be a string")

    project_name = project_name.strip()
    if not project_name or project_name in {".", ".."}:
        raise ValueError("不合法的项目名称。")
    if any(c in project_name for c in ("/", "\\", "..")):
        raise ValueError("不合法的项目名称，禁止包含路径穿越或路径分隔符。")
    # Reject non-ASCII to avoid filename security blocks on the Agnes platform
    if not project_name.isascii():
        raise ValueError("项目名称必须仅包含 ASCII 字符。")

    if sub_dir:
        if sub_dir not in ALLOWED_SUBDIRS:
            raise ValueError(f"不合法的媒体目录: {sub_dir}")

    target = WORKSPACE_ROOT / project_name
    if sub_dir:
        target = target / sub_dir
    target.mkdir(parents=True, exist_ok=True)

    real_target = target.resolve()
    try:
        real_target.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise PermissionError(
            "【安全拦截】检测到越界文件访问请求，已被系统拦截！"
        ) from None
    return real_target


def safe_leaf_filename(file_name: str, default_suffix: str = "") -> str:
    """Return a path-stripped filename with a safe default suffix.

    Strips directory components, validates the name, and appends a default
    extension if the filename has none.
    """
    if not isinstance(file_name, str):
        raise ValueError("file_name must be a string")

    leaf = Path(file_name.strip()).name
    if not leaf or leaf in {".", ".."}:
        raise ValueError("不合法的文件名。")
    if leaf.endswith(("/", "\\")) or "\x00" in leaf:
        raise ValueError("不合法的文件名。")
    # Reject non-ASCII filenames — Agnes platform security blocks them
    if not leaf.isascii():
        raise ValueError("文件名必须仅包含 ASCII 字符。")
    if "." not in leaf and default_suffix:
        leaf = f"{leaf}{default_suffix}"
    return leaf
