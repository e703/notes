#!/usr/bin/env python3
"""
Agnes Video v2.0 — Video Generation CLI (text-to-video / image-to-video / keyframes).

Usage:
    # Text-to-video
    python3 scripts/generate_video.py --project my_project --prompt "A cat walking on the beach" \\
        --output intro.mp4

    # Image-to-video (ti2vid)
    python3 scripts/generate_video.py --project my_project --prompt "Cat starts skateboarding" \\
        --ref-image sources/images/cat.jpg --output skateboard.mp4

    # Keyframe animation
    python3 scripts/generate_video.py --project my_project --prompt "Smooth transitions" \\
        --ref-url https://example.com/frame1.jpg --ref-url https://example.com/frame2.jpg \\
        --keyframes --output transition.mp4

    # Custom duration
    python3 scripts/generate_video.py --project my_project --prompt "..." --output clip.mp4 \\
        --num-frames 241 --frame-rate 24    # ≈10 seconds

Environment:
    AGNES_API_KEY          (required)   Agnes AI API key
    AGNES_VIDEO_MODEL      (optional)   Model ID (default: agnes-video-v2.0)
    AGNES_API_BASE         (optional)   API base URL (default: https://apihub.agnes-ai.com)
    AGNES_VIDEO_TIMEOUT    (optional)   Request timeout in seconds (default: 300)
    AGNES_POLL_INTERVAL    (optional)   Poll interval in seconds (default: 30)
    AGNES_MAX_POLLS        (optional)   Max polling attempts (default: 60)
    AGNES_WORKSPACE_ROOT   (optional)   Output root directory (default: ~/workspace)

Exit codes:
    0   Success, video downloaded
    1   Error / failure
    2   Timeout, task still processing
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "agnes-video-v2.0"
DEFAULT_API_BASE = "https://apihub.agnes-ai.com"
DEFAULT_TIMEOUT = 300
DEFAULT_POLL_INTERVAL = 30
DEFAULT_MAX_POLLS = 60
DEFAULT_WORKSPACE = os.path.expanduser("~/workspace")
DEFAULT_WIDTH = 1152
DEFAULT_HEIGHT = 768
DEFAULT_NUM_FRAMES = 121
DEFAULT_FRAME_RATE = 24


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _env(key: str, default: str = "") -> str:
    """Get env var, handling literal ${{VAR}} expansion in cron contexts."""
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


def _get_api_key() -> str:
    key = _env("AGNES_API_KEY")
    if not key or "${" in key:
        print("ERROR: AGNES_API_KEY not set or invalid", file=sys.stderr)
        sys.exit(1)
    return key


def _image_to_data_uri(path: str) -> str:
    """Convert a local image file to a data URI string."""
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def _extract_real_video_id(encoded: str) -> str | None:
    """Decode base64-encoded video_id from POST response."""
    import re
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


# ---------------------------------------------------------------------------
# API Calls
# ---------------------------------------------------------------------------
def submit_video(payload: dict, api_key: str, timeout: int) -> dict:
    """POST /v1/videos to submit a generation task."""
    api_base = _env("AGNES_API_BASE", DEFAULT_API_BASE)
    url = f"{api_base}/v1/videos"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = str(e)
        return {"ok": False, "status": e.code, "error": detail}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)}


def poll_video_status(video_id: str, api_key: str) -> dict:
    """GET /agnesapi?video_id= to check task status."""
    api_base = _env("AGNES_API_BASE", DEFAULT_API_BASE)
    url = f"{api_base}/agnesapi?video_id={video_id}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = str(e)
        return {"error": f"HTTP {e.code}", "detail": detail}
    except Exception as e:
        return {"error": str(e)}


def download_video(url: str, output_path: str, timeout: int = 180) -> int:
    """Download video from URL to local path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agnes-media-kit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if data.startswith(b"<?xml") or len(data) < 1000:
            raise ValueError(f"Downloaded non-video content ({len(data)} bytes)")
        with open(output_path, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args(argv: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agnes Video v2.0 — Text-to-Video / Image-to-Video / Keyframes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project my_project --prompt "A cat walking on beach" --output cat.mp4
  %(prog)s --project my_project --prompt "Skateboarding" --ref-image cat.jpg --output skate.mp4
  %(prog)s --project my_project --prompt "Transitions" --ref-url f1.jpg --ref-url f2.jpg --keyframes --output anim.mp4
  %(prog)s --project my_project --prompt "Slow motion" --output slomo.mp4 --num-frames 81 --frame-rate 16
        """,
    )
    parser.add_argument("--project", "-p", required=True,
                        help="Project directory slug (ASCII only, no slashes)")
    parser.add_argument("--prompt", "-P", required=True,
                        help="Video description or action instruction")
    parser.add_argument("--output", "-o", required=True,
                        help="Output filename (e.g. intro.mp4)")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                        help=f"Video width (default: {DEFAULT_WIDTH})")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT,
                        help=f"Video height (default: {DEFAULT_HEIGHT})")
    parser.add_argument("--num-frames", type=int, default=DEFAULT_NUM_FRAMES,
                        help=f"Total frames. Must be 8n+1: 81, 121, 241, 441 (max 441). Default: {DEFAULT_NUM_FRAMES}")
    parser.add_argument("--frame-rate", type=int, default=DEFAULT_FRAME_RATE,
                        help=f"Frames per second (1-60). Default: {DEFAULT_FRAME_RATE}")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible results")
    parser.add_argument("--negative-prompt", default=None,
                        help="Describe what to avoid in the video")
    parser.add_argument("--steps", type=int, default=None,
                        help="Number of inference steps")

    # Reference images
    ref_group = parser.add_mutually_exclusive_group()
    ref_group.add_argument("--ref-image", default=None,
                           help="Local reference image path (for image-to-video / ti2vid)")
    ref_group.add_argument("--ref-url", default=None,
                           help="Reference image URL (for ti2vid or first keyframe)")

    parser.add_argument("--keyframe-urls", nargs="*", default=None,
                        help="Additional keyframe image URLs (for keyframe animation mode)")
    parser.add_argument("--keyframes", action="store_true",
                        help="Enable keyframe animation mode (uses all ref URLs)")

    parser.add_argument("--poll-interval", type=int, default=None,
                        help=f"Poll interval in seconds (default: {DEFAULT_POLL_INTERVAL})")
    parser.add_argument("--max-polls", type=int, default=None,
                        help=f"Max polling attempts (default: {DEFAULT_MAX_POLLS})")
    parser.add_argument("--timeout", type=int, default=None,
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--no-wait", action="store_true",
                        help="Submit and exit without polling (save task_id for later)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the payload but don't send")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed progress")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    api_key = _get_api_key()

    # Validate project
    project = args.project
    if not project.replace("-", "").replace("_", "").isalnum():
        print(f"ERROR: Invalid project name '{project}'. Use ASCII-only slug.", file=sys.stderr)
        sys.exit(1)

    # Validate filename
    fname = args.output
    if not all(c.isascii() for c in fname) or "/" in fname or "\\" in fname:
        print(f"ERROR: Invalid filename '{fname}'. ASCII only.", file=sys.stderr)
        sys.exit(1)

    # Build paths
    workspace = os.path.expanduser(_env("AGNES_WORKSPACE_ROOT", DEFAULT_WORKSPACE))
    output_path = os.path.join(workspace, project, "target", "videos", args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Validate num_frames: must be 8n+1, max 441
    nf = args.num_frames
    if nf > 441:
        print(f"ERROR: num_frames {nf} exceeds max 441", file=sys.stderr)
        sys.exit(1)
    if (nf - 1) % 8 != 0:
        print(f"WARNING: num_frames {nf} is not 8n+1. Recommended: 81, 121, 241, 441", file=sys.stderr)

    timeout = args.timeout or int(_env("AGNES_VIDEO_TIMEOUT", str(DEFAULT_TIMEOUT)))
    poll_interval = args.poll_interval or int(_env("AGNES_POLL_INTERVAL", str(DEFAULT_POLL_INTERVAL)))
    max_polls = args.max_polls or int(_env("AGNES_MAX_POLLS", str(DEFAULT_MAX_POLLS)))

    # -----------------------------------------------------------------------
    # Build payload
    # -----------------------------------------------------------------------
    payload = {
        "model": _env("AGNES_VIDEO_MODEL", DEFAULT_MODEL),
        "prompt": args.prompt,
        "width": args.width,
        "height": args.height,
        "num_frames": nf,
        "frame_rate": args.frame_rate,
    }

    # Optional parameters
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.negative_prompt is not None:
        payload["negative_prompt"] = args.negative_prompt
    if args.steps is not None:
        payload["num_inference_steps"] = args.steps

    # Reference images
    image_urls: list[str] = []

    if args.ref_image:
        # Local file → data URI
        data_uri = _image_to_data_uri(args.ref_image)
        payload["mode"] = "ti2vid"
        payload["image"] = data_uri  # top-level string for ti2vid
        mode_str = "image-to-video (ti2vid)"
    elif args.ref_url:
        if args.keyframes:
            # Keyframe animation mode
            image_urls.append(args.ref_url)
            if args.keyframe_urls:
                image_urls.extend(args.keyframe_urls)
            payload["extra_body"] = {"mode": "keyframes", "image": image_urls}
            mode_str = f"keyframe animation ({len(image_urls)} frames)"
        else:
            # Single image → ti2vid
            payload["mode"] = "ti2vid"
            payload["image"] = args.ref_url  # top-level string
            mode_str = "image-to-video (ti2vid)"
    else:
        mode_str = "text-to-video"

    if args.verbose:
        seconds = nf / args.frame_rate
        print(f"[info] Project: {project}")
        print(f"[info] Mode: {mode_str}")
        print(f"[info] Output: {output_path}")
        print(f"[info] Resolution: {args.width}x{args.height}")
        print(f"[info] Frames: {nf} @ {args.frame_rate}fps = {seconds:.1f}s")
        print(f"[info] Poll interval: {poll_interval}s, max polls: {max_polls}")

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Submit
    # -----------------------------------------------------------------------
    print(f"[1/4] Submitting {mode_str} task...")
    result = submit_video(payload, api_key, timeout)

    if not result["ok"]:
        print(f"  Submission failed: HTTP {result['status']}", file=sys.stderr)
        print(json.dumps(result.get("error", ""), indent=2, ensure_ascii=False))
        sys.exit(1)

    body = result["body"]
    video_id_raw = body.get("video_id", "")
    task_id = body.get("task_id") or body.get("id", "")
    print(f"  task_id: {task_id}")
    print(f"  video_id (raw): {video_id_raw[:60]}...")

    if not video_id_raw:
        print("ERROR: No video_id in response", file=sys.stderr)
        print(json.dumps(body, indent=2, ensure_ascii=False))
        sys.exit(1)

    # Extract real video_id
    real_video_id = _extract_real_video_id(video_id_raw) or video_id_raw
    print(f"  video_id (decoded): {real_video_id}")

    # Save lightweight task info (no data URI = small file)
    info = {
        "task_id": task_id,
        "video_id_raw": video_id_raw,
        "video_id": real_video_id,
        "mode": mode_str,
        "num_frames": nf,
        "frame_rate": args.frame_rate,
        "prompt": args.prompt,
    }
    info_path = os.path.join(os.path.dirname(output_path), "task_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(f"  Task info saved: {info_path}")

    if args.no_wait:
        print(f"\n⏳ Task submitted. Check later with:")
        print(f"   python3 scripts/check_task.py {real_video_id}")
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Poll for completion
    # -----------------------------------------------------------------------
    print(f"[2/4] Polling for completion ({poll_interval}s interval)...")
    status_url = f"{_env('AGNES_API_BASE', DEFAULT_API_BASE)}/agnesapi?video_id={real_video_id}"

    result_data = None
    for attempt in range(1, max_polls + 1):
        print(f"  Poll {attempt}/{max_polls}...", end=" ", flush=True)
        time.sleep(poll_interval)

        status = poll_video_status(real_video_id, api_key)
        s = status.get("status", "unknown")
        p = status.get("progress", 0)
        print(f"Status: {s}, Progress: {p}%")
        if args.verbose:
            print(f"    Detail: {json.dumps(status, indent=2, ensure_ascii=False)}")

        if s == "completed":
            result_data = status
            break
        if s == "failed":
            print(f"    FAILED: {status.get('error', 'unknown error')}", file=sys.stderr)
            sys.exit(1)

    if not result_data:
        print(f"  Max polls ({max_polls}) reached. Task still processing.", file=sys.stderr)
        print(f"  Check later: python3 scripts/check_task.py {real_video_id}", file=sys.stderr)
        sys.exit(2)

    # Save result metadata
    meta_path = os.path.join(os.path.dirname(output_path), "result_info.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"  Result info saved: {meta_path}")

    # -----------------------------------------------------------------------
    # Download
    # -----------------------------------------------------------------------
    print(f"[3/4] Downloading video...")
    download_url = result_data.get("url", "")
    if not download_url:
        print("  Task completed but no download URL found", file=sys.stderr)
        sys.exit(1)

    bytes_written = download_video(download_url, output_path)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    seconds = result_data.get("seconds", f"{nf/args.frame_rate:.1f}")
    size_str = result_data.get("size", f"{args.width}x{args.height}")
    perf = result_data.get("perf_infer_s", "?")
    size_mapping = result_data.get("size_mapping", {})

    print(f"[4/4] Done!")
    print(f"\n✅ Video saved: {output_path}")
    print(f"   Size: {bytes_written:,} bytes ({bytes_written/1024/1024:.1f} MB)")
    print(f"   Duration: {seconds}s")
    print(f"   Resolution: {size_str}")
    print(f"   Inference time: {perf}s")

    if size_mapping.get("adjusted"):
        print(f"   Resolution mapping: {size_mapping['requested_width']}x{size_mapping['requested_height']} → {size_mapping['width']}x{size_mapping['height']} ({size_mapping['resolution']} {size_mapping['ratio']})")

    sys.exit(0)


if __name__ == "__main__":
    main()