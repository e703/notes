"""Handlers for the Agnes media router plugin.

Exports two tool handlers:
    generate_image_via_pic01  — text-to-image generation
    generate_video_via_mov01  — text-to-video generation

Configuration is read from environment variables or plugin.yaml defaults.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .workspace_manager import get_and_validate_project_path, safe_leaf_filename

# ---------------------------------------------------------------------------
# API configuration — all overridable via environment variables
# ---------------------------------------------------------------------------
IMAGE_ENDPOINT = os.getenv(
    "AGNES_IMAGE_ENDPOINT",
    "https://apihub.agnes-ai.com/v1/images/generations",
)
VIDEO_ENDPOINT = os.getenv(
    "AGNES_VIDEO_ENDPOINT",
    "https://apihub.agnes-ai.com/v1/videos",
)
IMAGE_MODEL = os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.0-flash")
VIDEO_MODEL = os.getenv("AGNES_VIDEO_MODEL", "agnes-video-v2.0")

IMAGE_REQUEST_TIMEOUT = int(os.getenv("AGNES_IMAGE_TIMEOUT", "180"))
VIDEO_REQUEST_TIMEOUT = int(os.getenv("AGNES_VIDEO_TIMEOUT", "300"))
DOWNLOAD_TIMEOUT = int(os.getenv("AGNES_DOWNLOAD_TIMEOUT", "300"))

MAX_RETRIES = int(os.getenv("AGNES_MAX_RETRIES", "2"))
RETRY_DELAY = float(os.getenv("AGNES_RETRY_DELAY", "3"))

USER_AGENT = "Hermes-Agent-Agnes-Router/1.1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _api_key() -> str:
    """Retrieve the Agnes API key from environment."""
    key = os.getenv("AGNES_API_KEY") or os.getenv("API_KEY")
    if not key:
        raise RuntimeError("AGNES_API_KEY or API_KEY is not configured")
    return key


def _post_json(
    url: str, payload: dict[str, Any], timeout: int = 180
) -> dict[str, Any]:
    """POST JSON to an endpoint with retry logic."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as exc:
            last_err = exc
            body = exc.read().decode("utf-8", errors="replace")[:2000]
            # Retryable status codes
            if exc.code in (429, 500, 502, 503, 504):
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
            raise RuntimeError(f"HTTP {exc.code} from Agnes API: {body}") from exc
        except urllib.error.URLError as exc:
            last_err = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            raise RuntimeError(f"Agnes API connection failed: {exc}") from exc
    else:
        raise RuntimeError(f"Request failed after {MAX_RETRIES + 1} attempts") from last_err

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError(f"Non-JSON response from Agnes API: {body[:1000]}") from None
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected JSON type from API: {type(parsed).__name__}")
    return parsed


def _download(url: str, timeout: int = 300) -> bytes:
    """Download content from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Download HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc


def _extract_url(data: dict[str, Any]) -> str | None:
    """Extract a download URL from API response, trying multiple key names."""
    if isinstance(data.get("url"), str):
        return data["url"]
    if isinstance(data.get("output_url"), str):
        return data["output_url"]
    items = data.get("data")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            for key in ("url", "image_url", "video_url", "output_url"):
                if isinstance(first.get(key), str):
                    return first[key]
    return None


def _extract_b64(data: dict[str, Any]) -> str | None:
    """Extract base64 content from API response."""
    items = data.get("data")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            for key in ("b64_json", "base64", "image_base64", "video_base64"):
                if isinstance(first.get(key), str):
                    return first[key]
    for key in ("b64_json", "base64", "image_base64", "video_base64"):
        if isinstance(data.get(key), str):
            return data[key]
    return None


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------
def generate_image_via_pic01(args: dict, **kwargs) -> str:
    """Generate an image via Agnes and save it in the safe project workspace."""
    try:
        project_name = str(args.get("project_name", "")).strip()
        prompt = str(args.get("prompt", "")).strip()
        file_name = str(args.get("file_name", "")).strip()
        size = str(args.get("size") or "1024x1024").strip()

        if not prompt:
            return _json_response({"ok": False, "error": "prompt is required"})

        save_dir = get_and_validate_project_path(project_name, "images")
        safe_name = safe_leaf_filename(file_name, ".png")
        target = save_dir / safe_name

        payload = {
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }
        result = _post_json(IMAGE_ENDPOINT, payload, timeout=IMAGE_REQUEST_TIMEOUT)
        remote_url = _extract_url(result)
        b64 = _extract_b64(result)

        if remote_url:
            content = _download(remote_url, timeout=DOWNLOAD_TIMEOUT)
        elif b64:
            content = base64.b64decode(b64)
        else:
            return _json_response({
                "ok": False,
                "message": "Agnes image task returned no direct URL/base64 payload",
                "raw": result,
            })

        target.write_bytes(content)
        return _json_response({
            "ok": True,
            "service": "pic_01",
            "model": IMAGE_MODEL,
            "path": str(target),
            "relative_path": f"~/workspace/{project_name}/images/{safe_name}",
            "remote_url": remote_url,
            "bytes": len(content),
        })

    except (ValueError, PermissionError) as exc:
        return _json_response({
            "ok": False,
            "security_blocked": True,
            "error": f"【安全拦截】{exc}",
        })
    except Exception as exc:
        return _json_response({
            "ok": False,
            "service": "pic_01",
            "error": str(exc),
        })


def generate_video_via_mov01(args: dict, **kwargs) -> str:
    """Generate a video via Agnes and save it in the safe project workspace."""
    try:
        project_name = str(args.get("project_name", "")).strip()
        prompt = str(args.get("prompt", "")).strip()
        file_name = str(args.get("file_name", "")).strip()

        if not prompt:
            return _json_response({"ok": False, "error": "prompt is required"})

        save_dir = get_and_validate_project_path(project_name, "videos")
        safe_name = safe_leaf_filename(file_name, ".mp4")
        target = save_dir / safe_name

        payload = {
            "model": VIDEO_MODEL,
            "prompt": prompt,
        }
        result = _post_json(
            VIDEO_ENDPOINT, payload, timeout=VIDEO_REQUEST_TIMEOUT
        )
        remote_url = _extract_url(result)
        b64 = _extract_b64(result)

        if remote_url:
            content = _download(remote_url, timeout=DOWNLOAD_TIMEOUT)
        elif b64:
            content = base64.b64decode(b64)
        else:
            # Video tasks are often async — return task info for polling
            return _json_response({
                "ok": False,
                "message": "Agnes video task submitted (async), returned no direct payload",
                "raw": result,
            })

        target.write_bytes(content)
        return _json_response({
            "ok": True,
            "service": "mov_01",
            "model": VIDEO_MODEL,
            "path": str(target),
            "relative_path": f"~/workspace/{project_name}/videos/{safe_name}",
            "remote_url": remote_url,
            "bytes": len(content),
        })

    except (ValueError, PermissionError) as exc:
        return _json_response({
            "ok": False,
            "security_blocked": True,
            "error": f"【安全拦截】{exc}",
        })
    except Exception as exc:
        return _json_response({
            "ok": False,
            "service": "mov_01",
            "error": str(exc),
        })
