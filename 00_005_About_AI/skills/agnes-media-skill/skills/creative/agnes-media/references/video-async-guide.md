# Video Generation Async Guide

## Overview

Video generation via `generate_video_via_mov01` is asynchronous. The tool submits
a task to the Agnes platform and returns immediately with a task ID. The actual
video is processed server-side and becomes available after a delay.

## Response Patterns

### Immediate Submission (Most Common)

```json
{
  "ok": false,
  "message": "Agnes video task submitted (async), returned no direct payload",
  "raw": {
    "task_id": "task_abc123def",
    "video_id": "xyz789...",
    "status": "queued",
    "progress": 0,
    "seconds": "5.0",
    "size": "1280x704"
  }
}
```

**This is normal.** `ok: false` here means "task queued, not yet complete."

### Immediate Completion (Rare)

Sometimes the video is generated so quickly that the payload is returned inline:

```json
{
  "ok": true,
  "service": "mov_01",
  "model": "agnes-video-v2.0",
  "path": "/home/alan/workspace/project/videos/output.mp4",
  "remote_url": "https://...",
  "bytes": 5678901
}
```

## Polling Workflow

### ⚠️ 关键：不要用 task_id 查状态

**`GET /v1/videos/{task_id}` 这个 endpoint 不返回任务结果**，即使视频已完成也一直显示 `queued`。

**必须** 用 `GET /agnesapi?video_id=<real_video_id>` 查询。`video_id` 来自 POST 创建任务的返回值（base64编码的字段），通过 `check_task.py` 自动解码即可。

### Method 1: Using check_task.py (Recommended)

```bash
# Check status — 传 video_id（POST返回的原始字段或解码后的都行）
python3 scripts/check_task.py video_d39354f7bafe484cac4c58481d91c171

# 也支持 base64 编码的原始 video_id
python3 scripts/check_task.py "video_bGl0ZWxsbTpjdXN0b21fbGxtX3Byb3ZpZGVy..."

# Exit codes:
#   0 = completed with download URL
#   1 = error
#   2 = still processing
```

### Method 2: Direct API Query (正确方式)

```bash
curl -s "https://apihub.agnes-ai.com/agnesapi?video_id=video_d39354f7bafe484cac4c58481d91c171" \
  -H "Authorization: Bearer ***"
```

> ⚠️ **不要用** `https://apihub.agnes-ai.com/v1/videos/{task_id}` — 这个 endpoint 不返回正确结果。

Response:

```json
{
  "status": "completed",
  "progress": 100,
  "url": "https://cdn.agnes-ai.com/videos/abc123.mp4",
  "video_id": "xyz789",
  "seconds": "5.0",
  "size": "1280x704"
}
```

### Full Completed Response (Real Example)

When the task completes, the response includes rich metadata:

```json
{
  "id": "task_abc123def",
  "status": "completed",
  "progress": 100,
  "url": "https://platform-outputs.agnes-ai.space/videos/.../video_xxx.mp4",
  "video_id": "video_xxx",
  "seconds": "5.0",
  "size": "1088x832",
  "model": "agnes-video-v2.0",
  "perf_infer_s": 70.8,
  "perf_infer_t0": 589215.4,
  "perf_output_size": 2858996,
  "perf_upload_s": 5.5,
  "perf_params": {
    "frame_rate": 24,
    "height": 832,
    "num_frames": 121,
    "num_inference_steps": 8,
    "seed": 436991,
    "width": 1088
  },
  "request_params": {
    "prompt": "...",
    "negative_prompt": "pc game, console game ...",
    "model": "agnes-video-v2.0",
    "num_frames": 121,
    "num_inference_steps": 8,
    "seed": 436991,
    "mode": "ti2vid",
    "ratio": "4:3",
    "resolution": "720p"
  },
  "size_mapping": {
    "adjusted": true,
    "height": 832,
    "width": 1088,
    "resolution": "720p",
    "ratio": "4:3",
    "requested_height": 768,
    "requested_width": 1152,
    "message": "Input size ... was mapped to nearest preset 720p/4:3 (1088x832)"
  },
  "prompt_id": "81db27d1-...",
  "created_at": 1783580591,
  "completed_at": 1783580667
}
```

### Method 3: Directory Polling

```bash
# Check if output file exists and is non-empty
while [ ! -s "/home/alan/workspace/project/videos/output.mp4" ]; do
  echo "Still generating..."
  sleep 60
done
echo "Done!"
```

## Download Pattern

```bash
# 1. Get the URL using correct endpoint
TASK_RESULT=$(curl -s "https://apihub.agnes-ai.com/agnesapi?video_id=video_d39354f7bafe484cac4c58481d91c171" \
  -H "Authorization: Bearer ***")

# 2. Extract URL (avoid inline python — write to temp file if needed)
URL=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))")

# 3. Only download if URL exists
if [ -n "$URL" ]; then
  curl -L -o "/home/alan/workspace/project/videos/output.mp4" "$URL"
else
  echo "Task completed but no download URL available"
fi
```

## Cron-Based Notification

For automated workflows, set up a recurring cron job:

```yaml
schedule: "2m"
prompt: |
  Check if /home/alan/workspace/myproject/videos/intro.mp4 exists and is larger than 1000 bytes.
  If yes, report: "Video ready: /home/alan/workspace/myproject/videos/intro.mp4"
  If not, report: "Still generating... elapsed time estimate needed."
deliver: "origin"
```

## Common Issues

### Task Completed But No URL

Some tasks show `status: completed` and `progress: 100` but return no `url` field.
This means the video was generated on the platform but the download link has expired.

**Solution**: Resubmit the video generation with the same or a refined prompt.

### 127-Byte XML Error Files

A failed download produces a tiny XML file containing `<Error><Code>NoSuchKey</Code>`.

**Solution**: Always verify the URL exists before downloading. Remove these files.

### API Key Expansion in Cron

In cron sessions, `$AGNES_API_KEY` may expand to the literal string `${AGNES_API_KEY}`.

**Solution**: Use `scripts/check_task.py` which handles extraction automatically, or:

```bash
REAL_KEY=$(cat /proc/$$/environ | tr '\0' '\n' | grep '^AGNES_API_KEY=' | cut -d= -f2)
```

### Rate Limiting (HTTP 429)

The Agnes API enforces rate limits on status queries.

**Solution**: Wait at least 60 seconds between polls. The plugin's retry logic handles this.

### Video Processing Time

Typical processing times:
- Simple prompts: 1-3 minutes
- Complex scenes: 3-10 minutes
- High resolution: 5-15 minutes

## API Key Sourcing

The plugin checks these sources in order:
1. `AGNES_API_KEY` environment variable
2. `API_KEY` environment variable (fallback)

In Hermes config, the key is typically stored as:
```yaml
custom_providers:
  - name: Apihub.agnes-ai.com
    base_url: https://apihub.agnes-ai.com/v1
    api_key: sk-...
```

And the plugin receives it via the `AGNES_API_KEY` environment variable.
