#!/usr/bin/env python3
"""
Batch image generation with queue-aware retry logic.

Waits through 503 queue-full errors and retries each image sequentially.
Only one request is in flight at a time — parallel requests all hit the
same queue-full condition.

Usage:
    # Edit the TASKS list below, then:
    python3 scripts/batch_generate.py

    # Or use a JSON file:
    python3 scripts/batch_generate.py --tasks tasks.json

tasks.json format (in .hermes/skills/creative/agnes-media/templates/):
    [
        {
            "prompt": "A cat on a white background...",
            "output": "target/images/cat_01.jpg",
            "ref_image": "sources/images/ref_cat.jpg"    // optional
        },
        ...
    ]

Environment:
    AGNES_API_KEY          (required)
    AGNES_IMAGE_MODEL      (optional)   Default: agnes-image-2.0-flash
    AGNES_API_BASE         (optional)   Default: https://apihub.agnes-ai.com
    AGNES_IMAGE_TIMEOUT    (optional)   Default: 180
    AGNES_MAX_RETRIES      (optional)   Default: 15
    AGNES_RETRY_DELAY      (optional)   Default: 30
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = ""
API_BASE = "https://apihub.agnes-ai.com"
MODEL = "agnes-image-2.0-flash"
TIMEOUT = 180
MAX_ATTEMPTS = 15
RETRY_DELAY = 30

# ---------------------------------------------------------------------------
# FILL THIS IN for inline usage — or use --tasks <file.json>
# ---------------------------------------------------------------------------
TASKS: list[dict] = [
    # Example:
    # {
    #     "prompt": "A silver tabby cat on a studio background, soft lighting, centered...",
    #     "output": "target/images/cat_01.jpg",
    #     # "ref_image": "sources/images/ref_cat.jpg",   # optional, for image-to-image
    # },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def image_to_data_uri(path: str) -> str:
    path = os.path.expanduser(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def build_payload(task: dict) -> dict:
    extra_body = {"response_format": "url"}
    ref = task.get("ref_image") or task.get("ref")
    if ref:
        extra_body["image"] = [image_to_data_uri(ref)]
    return {
        "model": MODEL,
        "prompt": task["prompt"],
        "size": task.get("size", "1024x1024"),
        "extra_body": extra_body,
    }


def send_request(payload: dict) -> tuple[int, dict]:
    url = f"{API_BASE}/v1/images/generations"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {"raw": str(e)}
        return e.code, detail
    except Exception as e:
        return 0, {"error": str(e)}


def download(url: str, path: str) -> int:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "agnes-media-kit/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    global API_KEY, API_BASE, MODEL, TIMEOUT, MAX_ATTEMPTS, RETRY_DELAY

    parser = argparse.ArgumentParser(
        description="Batch image generation with queue retry",
    )
    parser.add_argument("--tasks", "-t", metavar="FILE.json",
                        help="Load tasks from JSON file instead of hardcoded list")
    parser.add_argument("--max-attempts", type=int, default=None,
                        help=f"Max retry attempts per image (default: {MAX_ATTEMPTS})")
    parser.add_argument("--retry-delay", type=int, default=None,
                        help=f"Delay between retries (default: {RETRY_DELAY})")
    parser.add_argument("--project", "-p", default="batch_project",
                        help="Project name for output path resolution")
    args = parser.parse_args()

    API_KEY = _env("AGNES_API_KEY")
    if not API_KEY or "${" in API_KEY:
        print("ERROR: AGNES_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    MODEL = _env("AGNES_IMAGE_MODEL", MODEL)
    API_BASE = _env("AGNES_API_BASE", API_BASE)
    TIMEOUT = int(_env("AGNES_IMAGE_TIMEOUT", str(TIMEOUT)))
    MAX_ATTEMPTS = args.max_attempts or int(_env("AGNES_MAX_RETRIES", str(MAX_ATTEMPTS)))
    RETRY_DELAY = args.retry_delay or int(_env("AGNES_RETRY_DELAY", str(RETRY_DELAY)))

    # Load tasks
    if args.tasks:
        path = os.path.expanduser(args.tasks)
        with open(path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        tasks = TASKS

    if not tasks:
        print("No tasks defined. Either edit TASKS list or use --tasks <file.json>", file=sys.stderr)
        sys.exit(1)

    workspace = os.path.expanduser(_env("AGNES_WORKSPACE_ROOT", os.path.expanduser("~/workspace")))
    project = args.project

    # Resolve relative output paths
    resolved_tasks = []
    for t in tasks:
        out = t.get("output", "")
        if out and not os.path.isabs(out):
            out = os.path.join(workspace, project, out)
        resolved_tasks.append({**t, "output_path": out})

    print(f"Batch: {len(tasks)} image(s), max {MAX_ATTEMPTS} attempts each, {RETRY_DELAY}s delay")
    print(f"Model: {MODEL}")
    print(f"Project: {project}")
    print()

    pending = list(range(len(resolved_tasks)))
    attempts = [0] * len(resolved_tasks)
    results = [None] * len(resolved_tasks)

    while pending:
        idx = pending.pop(0)
        task = resolved_tasks[idx]
        attempts[idx] += 1
        ts = timestamp()

        print(f"\n{'='*60}")
        print(f"[{ts}] Image {idx+1}/{len(tasks)} | {os.path.basename(task['output_path'])} | "
              f"Attempt {attempts[idx]}/{MAX_ATTEMPTS}")
        print(f"{'='*60}")
        print(f"  Prompt: {task['prompt'][:100]}...")

        payload = build_payload(task)
        http_code, body = send_request(payload)
        print(f"  HTTP {http_code}")

        if http_code == 503:
            msg = body.get("error", {}).get("message", "queue full")
            print(f"  ✗ Queue full: {msg} — waiting {RETRY_DELAY}s...")
            pending.append(idx)
            time.sleep(RETRY_DELAY)
            continue

        if http_code == 200 or http_code == 201:
            try:
                data_list = body.get("data", [])
                if not data_list:
                    print("  ✗ Empty data array...")
                    pending.append(idx)
                    continue
                url = data_list[0].get("url", "")
                if not url:
                    print("  ✗ No URL in response")
                    pending.append(idx)
                    continue
                sz = download(url, task["output_path"])
                print(f"  ✓ Downloaded: {task['output_path']} ({sz:,} bytes)")
                results[idx] = sz
            except Exception as e:
                print(f"  ✗ Download error: {e}")
                pending.append(idx)
        else:
            msg = body.get("error", {}).get("message", str(body)[:200])
            print(f"  ✗ Error: {msg}")
            if attempts[idx] < MAX_ATTEMPTS:
                pending.append(idx)
                time.sleep(RETRY_DELAY)

        # Small pause between requests even on success
        if pending:
            time.sleep(1)

    # Summary
    print(f"\n{'='*60}")
    print("Final results:")
    ok = 0
    for i, task in enumerate(resolved_tasks):
        fname = os.path.basename(task["output_path"])
        if results[i]:
            print(f"  ✓ {fname}: {results[i]:,} bytes")
            ok += 1
        else:
            print(f"  ✗ {fname}: FAILED after {attempts[i]} attempts")

    print(f"\nDone: {ok}/{len(tasks)} succeeded.")
    sys.exit(0 if ok == len(tasks) else 1)


if __name__ == "__main__":
    main()