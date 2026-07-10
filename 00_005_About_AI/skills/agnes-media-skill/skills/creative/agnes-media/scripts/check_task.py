#!/usr/bin/env python3
"""Check Agnes video task status — CORRECT endpoint.

Usage:
    python3 check_task.py <video_id>           # e.g. video_d39354f7... (preferred)
    python3 check_task.py --task <task_id>       # extracts video_id from task

Returns JSON with task status, progress, and download URL if available.

ENDPOINT NOTE:
    The POST response includes a base64-encoded `video_id` field like:
      "video_bGl0ZWxsb..."  
    Decode it to get the real video_id (e.g. "video_d39354f7...").
    Query the CORRECT endpoint:  GET /agnesapi?video_id=<real_video_id>
    The old /v1/videos/{task_id} endpoint does NOT return task results.
"""

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request


def get_api_key() -> str:
    """Get API key, handling cron env var literal expansion."""
    key = os.environ.get("AGNES_API_KEY", "") or os.environ.get("API_KEY", "")
    if "${" in key:
        try:
            with open(f"/proc/{os.getpid()}/environ", "rb") as f:
                for line in f.read().split(b"\x00"):
                    if line.startswith(b"AGNES_API_KEY="):
                        key = line.split(b"=", 1)[1].decode()
                        break
        except Exception:
            pass
    return key


def extract_real_video_id(encoded: str) -> str | None:
    """Decode the base64-encoded video_id field from the POST response.

    The POST /v1/videos response returns:
      video_id: "video_<base64>"
    where the base64 decodes to:
      "litellm:custom_llm_provider:openai;model_id:agnes-video-v2.0;video_id:video_<real_id>"
    
    Returns the real video_id (e.g. "video_d39354f7...") or None if it can't parse it.
    """
    raw = encoded
    if raw.startswith("video_"):
        raw = raw[len("video_"):]
    try:
        decoded = base64.b64decode(raw).decode()
        m = re.search(r"video_id:(\S+)", decoded)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def query_video(video_id: str) -> dict:
    """Query the correct Agnes API endpoint for video results."""
    api_key = get_api_key()
    if not api_key or "${" in api_key:
        return {"error": "AGNES_API_KEY not available or invalid"}

    url = f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    # Handle --task <task_id> mode
    if arg == "--task" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        # Try to get the raw POST again — task_id alone won't work
        # User must pass the video_id from the POST response instead
        print(json.dumps({
            "error": "task_id alone is not sufficient. Use the video_id from the POST /v1/videos response instead.",
            "hint": "The POST response contains a 'video_id' field (base64-encoded). "
                     "Pass that field's value here and we'll auto-extract it, "
                     "or pass the decoded video_id directly (e.g. video_d39354f7...)."
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

    # Try to auto-extract real video_id from base64-encoded form
    video_id = arg
    if arg.startswith("video_") and len(arg) > 50:
        # Likely a base64-encoded video_id, try to extract
        extracted = extract_real_video_id(arg)
        if extracted:
            video_id = extracted

    result = query_video(video_id)
    result["_queried_with"] = video_id
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code based on status
    if result.get("status") == "completed" and result.get("url"):
        sys.exit(0)
    elif result.get("status") == "completed":
        sys.exit(0)
    elif "error" in result:
        sys.exit(1)
    else:
        sys.exit(2)  # Still processing


if __name__ == "__main__":
    main()
