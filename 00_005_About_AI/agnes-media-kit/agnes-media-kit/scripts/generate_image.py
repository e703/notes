#!/usr/bin/env python3
"""
Agnes Image 2.0 Flash — Text-to-Image & Image-to-Image Generation CLI.

Usage:
    # Text-to-image
    python3 scripts/generate_image.py --project my_project --prompt "A cat on a white background" --output cat.png

    # Image-to-image (with reference image URL)
    python3 scripts/generate_image.py --project my_project --prompt "Transform into summer" \\
        --ref-url https://example.com/cat.jpg --output cat_summer.png

    # Image-to-image (with local reference image)
    python3 scripts/generate_image.py --project my_project --prompt "Add a red bow" \\
        --ref-image sources/images/cat.jpg --output cat_bow.png

    # Multi-image composition
    python3 scripts/generate_image.py --project my_project --prompt "Battle scene" \\
        --ref-url https://example.com/char1.png --ref-url https://example.com/char2.png \\
        --output battle.png

    # Custom size
    python3 scripts/generate_image.py --project my_project --prompt "..." --output img.png --size 768x768

Environment:
    AGNES_API_KEY          (required)   Agnes AI API key
    AGNES_IMAGE_MODEL      (optional)   Model ID (default: agnes-image-2.0-flash)
    AGNES_API_BASE         (optional)   API base URL (default: https://apihub.agnes-ai.com)
    AGNES_IMAGE_TIMEOUT    (optional)   Request timeout in seconds (default: 180)
    AGNES_MAX_RETRIES      (optional)   Max retry attempts (default: 10)
    AGNES_RETRY_DELAY      (optional)   Retry delay in seconds (default: 30)
    AGNES_WORKSPACE_ROOT   (optional)   Output root directory (default: ~/workspace)

Exit codes:
    0   Success
    1   Error / failure
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
DEFAULT_MODEL = "agnes-image-2.0-flash"
DEFAULT_API_BASE = "https://apihub.agnes-ai.com"
DEFAULT_SIZE = "1024x1024"
DEFAULT_TIMEOUT = 180
DEFAULT_MAX_RETRIES = 10
DEFAULT_RETRY_DELAY = 30
DEFAULT_WORKSPACE = os.path.expanduser("~/workspace")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _env(key: str, default: str = "") -> str:
    """Get env var, handling literal ${VAR} expansion in cron contexts."""
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


def _parse_output_path(path: str) -> tuple:
    """Parse output path into (project_name, relative_path) or raise."""
    clean = path.replace("\\", "/")
    return os.path.basename(clean)


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


def _build_payload(args: argparse.Namespace) -> dict:
    """Build the request payload from CLI arguments."""
    extra_body: dict = {"response_format": "url"}
    image_urls: list = []

    # Collect reference images: --ref-url (raw URL)
    if args.ref_url:
        image_urls.extend(args.ref_url)

    # Collect reference images: --ref-image (local file → data URI)
    if args.ref_image:
        for path in args.ref_image:
            image_urls.append(_image_to_data_uri(path))

    if image_urls:
        extra_body["image"] = image_urls

    payload = {
        "model": _env("AGNES_IMAGE_MODEL", DEFAULT_MODEL),
        "prompt": args.prompt,
        "size": args.size or DEFAULT_SIZE,
        "extra_body": extra_body,
    }
    return payload


def _send_request(payload: dict, api_key: str, timeout: int) -> tuple:
    """Send POST request. Returns (http_status, response_dict, error_str)."""
    api_base = _env("AGNES_API_BASE", DEFAULT_API_BASE)
    url = f"{api_base}/v1/images/generations"

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
            return resp.status, body, None
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = str(e)
        return e.code, detail, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return 0, {}, f"Connection error: {e.reason}"
    except Exception as e:
        return 0, {}, str(e)


def _download_image(url: str, output_path: str, timeout: int = 120) -> int:
    """Download image from URL to local path. Returns bytes written."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agnes-media-kit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        # Verify it's actually an image (not error XML)
        if data.startswith(b"<?xml") or len(data) < 100:
            raise ValueError(f"Downloaded non-image content ({len(data)} bytes)")
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
        description="Agnes Image 2.0 Flash — Text-to-Image & Image-to-Image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project my_project --prompt "A cat" --output cat.png
  %(prog)s --project my_project --prompt "Edit this" --ref-url https://... --output edited.png
  %(prog)s --project my_project --prompt "Combine" --ref-image img1.jpg --ref-image img2.jpg --output combined.png
        """,
    )
    parser.add_argument("--project", "-p", required=True,
                        help="Project directory slug (ASCII only, no slashes)")
    parser.add_argument("--prompt", "-P", required=True,
                        help="Image description or edit instruction")
    parser.add_argument("--output", "-o", required=True,
                        help="Output filename (e.g. output.png, result.jpg)")
    parser.add_argument("--size", "-s", default=DEFAULT_SIZE,
                        help=f"Image dimensions WIDTHxHEIGHT (default: {DEFAULT_SIZE})")
    parser.add_argument("--ref-url", action="append", dest="ref_url", default=None,
                        help="Reference image URL (can be specified multiple times)")
    parser.add_argument("--ref-image", action="append", dest="ref_image", default=None,
                        help="Local reference image path (can be multiple; auto-converted to data URI)")
    parser.add_argument("--retries", type=int, default=None,
                        help=f"Max retry attempts (default: {DEFAULT_MAX_RETRIES})")
    parser.add_argument("--retry-delay", type=int, default=None,
                        help=f"Delay between retries in seconds (default: {DEFAULT_RETRY_DELAY})")
    parser.add_argument("--timeout", type=int, default=None,
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the payload but don't send the request")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed progress information")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    api_key = _get_api_key()

    # Validate project name
    project = args.project
    if not project.replace("-", "").replace("_", "").isalnum():
        print(f"ERROR: Invalid project name '{project}'. Use ASCII-only slug.", file=sys.stderr)
        sys.exit(1)

    # Build paths
    workspace = os.path.expanduser(_env("AGNES_WORKSPACE_ROOT", DEFAULT_WORKSPACE))
    output_path = os.path.join(workspace, project, "target", "images", args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Validate filename
    fname = args.output
    if not all(c.isascii() for c in fname) or "/" in fname or "\\" in fname:
        print(f"ERROR: Invalid filename '{fname}'. ASCII only, no path separators.", file=sys.stderr)
        sys.exit(1)

    timeout = args.timeout or int(_env("AGNES_IMAGE_TIMEOUT", str(DEFAULT_TIMEOUT)))
    max_retries = args.retries or int(_env("AGNES_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
    retry_delay = args.retry_delay or int(_env("AGNES_RETRY_DELAY", str(DEFAULT_RETRY_DELAY)))

    payload = _build_payload(args)

    # Determine generation mode for display
    ref_count = len(payload["extra_body"].get("image", []))
    if ref_count == 0:
        mode_str = "text-to-image"
    elif ref_count == 1:
        mode_str = "image-to-image"
    else:
        mode_str = f"multi-image ({ref_count} references)"

    if args.verbose:
        print(f"[info] Project: {project}")
        print(f"[info] Mode: {mode_str}")
        print(f"[info] Output: {output_path}")
        print(f"[info] Size: {args.size}")
        print(f"[info] Max retries: {max_retries}")
        print(f"[info] Retry delay: {retry_delay}s")

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # Send request with retry for 503 queue-full
    last_error = None
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"  Retry {attempt}/{max_retries} after {retry_delay}s...")
            time.sleep(retry_delay)

        http_code, body, error = _send_request(payload, api_key, timeout)
        if args.verbose:
            print(f"  HTTP {http_code} (attempt {attempt}/{max_retries})")

        if http_code == 503:
            # Queue full — retry
            msg = body.get("error", {}).get("message", "queue full")
            print(f"  Queue full: {msg} — waiting {retry_delay}s...")
            last_error = f"HTTP 503 after {attempt} attempts"
            continue

        if error:
            print(f"  Error: {error}")
            last_error = error
            continue

        if http_code == 200 or http_code == 201:
            try:
                data_list = body.get("data", [])
                if not data_list:
                    print("ERROR: Empty data array in response", file=sys.stderr)
                    last_error = "empty response"
                    continue

                result = data_list[0]
                download_url = result.get("url", "")

                if not download_url:
                    print("ERROR: No download URL in response", file=sys.stderr)
                    print(json.dumps(body, indent=2, ensure_ascii=False))
                    last_error = "no url"
                    continue

                bytes_written = _download_image(download_url, output_path)

                print(f"\n✅ Image saved: {output_path}")
                print(f"   Size: {bytes_written:,} bytes ({bytes_written/1024:.1f} KB)")
                print(f"   Mode: {mode_str}")
                if result.get("revised_prompt"):
                    print(f"   Revised prompt: {result['revised_prompt']}")
                sys.exit(0)

            except Exception as e:
                print(f"  Error processing response: {e}", file=sys.stderr)
                last_error = str(e)
                continue
        else:
            msg = body.get("error", {}).get("message", json.dumps(body, ensure_ascii=False))
            print(f"  Unexpected HTTP {http_code}: {msg[:200]}")
            last_error = f"HTTP {http_code}"
            continue

    print(f"\n❌ Failed after {max_retries} attempts. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()