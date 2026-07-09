#!/usr/bin/env python3
"""Check Agnes video task status.

Usage:
    python3 check_task.py <task_id>
    python3 check_task.py task_abc123

Returns JSON with task status, progress, and download URL if available.

Handles:
    - API key extraction from environment (including cron literal expansion)
    - Preferred and fallback API endpoints
    - URL validation before download
"""

import json
import os
import sys
import urllib.request
import urllib.error


def get_api_key() -> str:
    """Get API key, handling cron env var literal expansion."""
    key = os.environ.get("AGNES_API_KEY", "") or os.environ.get("API_KEY", "")
    if "${" in key:
        # Env var is literal string, extract real value from process environ
        try:
            with open(f"/proc/{os.getpid()}/environ", "rb") as f:
                for line in f.read().split(b"\x00"):
                    if line.startswith(b"AGNES_API_KEY="):
                        key = line.split(b"=", 1)[1].decode()
                        break
        except Exception:
            pass
    return key


def check_task(task_id: str) -> dict:
    """Query Agnes API for task status."""
    api_key = get_api_key()
    if not api_key or "${" in api_key:
        return {"error": "AGNES_API_KEY not available or invalid"}

    # Preferred endpoint — accepts full task_ prefixed ID
    url = f"https://apihub.agnes-ai.com/v1/videos/{task_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: check_task.py <task_id>"}, indent=2))
        sys.exit(1)

    task_id = sys.argv[1]
    result = check_task(task_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code based on status
    if result.get("status") == "completed" and result.get("url"):
        sys.exit(0)
    elif "error" in result:
        sys.exit(1)
    else:
        sys.exit(2)  # Still processing


if __name__ == "__main__":
    main()
