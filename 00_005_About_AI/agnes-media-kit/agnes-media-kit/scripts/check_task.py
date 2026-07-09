#!/usr/bin/env python3
"""
Check Agnes video task status — CORRECT endpoint.

Usage:
    python3 scripts/check_task.py <video_id>           # e.g. video_d39354f7...
    python3 scripts/check_task.py <base64_encoded_id>   # auto-extracts real ID
    python3 scripts/check_task.py --watch <video_id>    # poll until completion

Environment:
    AGNES_API_KEY     (required)   Agnes AI API key
    AGNES_API_BASE    (optional)   API base URL (default: https://apihub.agnes-ai.com)

Exit codes:
    0   Task completed (with or without download URL)
    1   Error
    2   Still processing
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request


def _env(key: str, default: str = "") -> str:
    val = os.environ.get(key, "") or default
    if "${" in val:
        try:
            with open(f"/proc/{os.getpid()}/environ", "rb") as f:
                for line in f.read().split(b"\x00"):
                    if line.startswith(f"{key}=".encode()):
                        val = line.split(b"=", 1)[1].decode()
                        break
        except Exception:
            pass
    return val


def get_api_key() -> str:
    key = _env("AGNES_API_KEY")
    if not key or "${" in key:
        print("ERROR: AGNES_API_KEY not available", file=sys.stderr)
        sys.exit(1)
    return key


def extract_real_video_id(encoded: str) -> str | None:
    """Decode base64-encoded video_id from POST response.

    The POST /v1/videos response returns:
      video_id: "video_<base64>"
    where the base64 decodes to:
      "litellm:custom_llm_provider:openai;model_id:agnes-video-v2.0;video_id:video_<real_id>"

    Returns the real video_id or None.
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


def query_video(video_id: str, api_key: str) -> dict:
    """Query the correct Agnes API endpoint for video results."""
    api_base = _env("AGNES_API_BASE", "https://apihub.agnes-ai.com")
    url = f"{api_base}/agnesapi?video_id={video_id}"

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


def format_result(result: dict) -> str:
    """Format a status result for human reading."""
    lines = []
    status = result.get("status", "unknown")
    progress = result.get("progress", 0)
    lines.append(f"Status: {status}")
    lines.append(f"Progress: {progress}%")

    if result.get("seconds"):
        lines.append(f"Duration: {result['seconds']}s")
    if result.get("size"):
        lines.append(f"Resolution: {result['size']}")
    if result.get("video_id"):
        lines.append(f"Video ID: {result['video_id']}")
    if result.get("url"):
        lines.append(f"Download URL: {result['url']}")
    if result.get("perf_infer_s"):
        lines.append(f"Inference time: {result['perf_infer_s']}s")
    if result.get("size_mapping"):
        sm = result["size_mapping"]
        if sm.get("adjusted"):
            lines.append(f"Resolution mapping: {sm.get('requested_width','?')}x{sm.get('requested_height','?')} "
                         f"→ {sm.get('width','?')}x{sm.get('height','?')} "
                         f"({sm.get('resolution','?')} {sm.get('ratio','?')})")
    if result.get("error"):
        lines.append(f"Error: {result['error']}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Agnes video task status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("video_id", nargs="?", help="Video ID (raw or base64-encoded)")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Poll repeatedly until completion")
    parser.add_argument("--interval", "-i", type=int, default=30,
                        help="Poll interval in seconds (default: 30)")
    parser.add_argument("--max-polls", type=int, default=60,
                        help="Max polling attempts (default: 60)")
    parser.add_argument("--raw", action="store_true",
                        help="Output raw JSON instead of formatted text")
    parser.add_argument("--download", "-d", metavar="OUTPUT_PATH",
                        help="Download the video to the specified path if completed")
    args = parser.parse_args()

    if not args.video_id:
        parser.print_help()
        print("\nProvide a video_id from the POST /v1/videos response.", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()
    video_id = args.video_id

    # Auto-extract from base64-encoded form
    if video_id.startswith("video_") and len(video_id) > 50:
        extracted = extract_real_video_id(video_id)
        if extracted:
            video_id = extracted

    if args.watch:
        print(f"Watching video_id: {video_id}")
        for attempt in range(1, args.max_polls + 1):
            print(f"  Poll {attempt}/{args.max_polls}...", end=" ", flush=True)
            result = query_video(video_id, api_key)
            s = result.get("status", "unknown")
            p = result.get("progress", 0)
            print(f"Status: {s}, Progress: {p}%")

            if s == "completed":
                if args.raw:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print(f"\n✅ Completed!")
                    print(format_result(result))
                if args.download and result.get("url"):
                    _do_download(result["url"], args.download)
                sys.exit(0)
            if s == "failed":
                print(f"FAILED: {result.get('error', 'unknown')}", file=sys.stderr)
                sys.exit(1)

            time.sleep(args.interval)

        print(f"\nMax polls ({args.max_polls}) reached.", file=sys.stderr)
        sys.exit(2)

    # Single check
    result = query_video(video_id, api_key)
    result["_queried_with"] = video_id

    if args.raw:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_result(result))
        if result.get("status") == "completed" and result.get("url"):
            print(f"\nTo download: python3 {__file__} {video_id} --download output.mp4")

    if args.download and result.get("status") == "completed" and result.get("url"):
        _do_download(result["url"], args.download)

    # Exit code
    status = result.get("status", "error")
    if status == "completed":
        sys.exit(0)
    elif "error" in result:
        sys.exit(1)
    else:
        sys.exit(2)


def _do_download(url: str, output_path: str) -> None:
    """Download and save a file."""
    import urllib.request
    output_path = os.path.expanduser(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    print(f"\nDownloading to {output_path}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agnes-media-kit/1.0"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
        if data.startswith(b"<?xml") or len(data) < 1000:
            print(f"ERROR: Downloaded non-video content ({len(data)} bytes)", file=sys.stderr)
            sys.exit(1)
        with open(output_path, "wb") as f:
            f.write(data)
        print(f"✅ Saved: {output_path} ({len(data)/1024/1024:.1f} MB)")
    except Exception as e:
        print(f"ERROR: Download failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()