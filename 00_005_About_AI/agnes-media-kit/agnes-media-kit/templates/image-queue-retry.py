#!/usr/bin/env python3
"""
Template: Image generation with queue-full retry logic.

This is a simplified version of batch_generate.py for single-image use.
Useful when the API returns 503 "image queue is full" errors.

Usage:
    export AGNES_API_KEY="sk-xxxx"
    python3 templates/image-queue-retry.py
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

# ─── 配置 ───────────────────────────────────────
API_KEY = os.environ.get("AGNES_API_KEY", "${AGNES_API_KEY}")
MODEL = "agnes-image-2.0-flash"
API_BASE = "https://apihub.agnes-ai.com"
SIZE = "1024x1024"
MAX_ATTEMPTS = 10
RETRY_DELAY = 30  # seconds

# ─── 任务 ───────────────────────────────────────
PROMPT = "A silver tabby cat on a white studio background, soft lighting, centered, high detail"
OUTPUT_PATH = "cat.png"  # 输出文件路径
REF_IMAGE = None  # 或 "sources/images/ref.jpg" 用于图生图

# ────────────────────────────────────────────────


def image_to_data_uri(path: str) -> str:
    path = os.path.expanduser(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp",
                ".gif": "image/gif", ".bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def main():
    if "${" in API_KEY:
        print("ERROR: AGNES_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build payload
    extra_body = {"response_format": "url"}
    if REF_IMAGE:
        extra_body["image"] = [image_to_data_uri(REF_IMAGE)]

    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "size": SIZE,
        "extra_body": extra_body,
    }

    print(f"Generating image...")
    print(f"  Model: {MODEL}")
    print(f"  Size: {SIZE}")
    print(f"  Prompt: {PROMPT[:80]}...")
    if REF_IMAGE:
        print(f"  Ref image: {REF_IMAGE}")
    print(f"  Max attempts: {MAX_ATTEMPTS}, Retry delay: {RETRY_DELAY}s")
    print()

    url = f"{API_BASE}/v1/images/generations"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"  Attempt {attempt}/{MAX_ATTEMPTS}...", end=" ", flush=True)

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
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                print(f"HTTP {resp.status}")

            download_url = body.get("data", [{}])[0].get("url", "")
            if not download_url:
                print("  ✗ No URL in response")
                time.sleep(RETRY_DELAY)
                continue

            # Download
            print(f"  Downloading...")
            req_dl = urllib.request.Request(download_url,
                                            headers={"User-Agent": "agnes-media-kit/1.0"})
            with urllib.request.urlopen(req_dl, timeout=120) as dl:
                img_data = dl.read()

            os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
            with open(OUTPUT_PATH, "wb") as f:
                f.write(img_data)

            print(f"\n✅ Image saved: {OUTPUT_PATH} ({len(img_data):,} bytes)")
            sys.exit(0)

        except urllib.error.HTTPError as e:
            if e.code == 503:
                print("HTTP 503 (queue full) — waiting...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"HTTP {e.code}")
                try:
                    detail = json.loads(e.read().decode("utf-8"))
                    print(f"  Error: {json.dumps(detail, indent=2, ensure_ascii=False)[:200]}")
                except Exception:
                    print(f"  {e}")
                time.sleep(RETRY_DELAY)
                continue

        except Exception as e:
            print(f"  ✗ {e}")
            time.sleep(RETRY_DELAY)
            continue

    print(f"\n❌ Failed after {MAX_ATTEMPTS} attempts.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()