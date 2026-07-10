# Agnes Media Skill

Hermes Agent plugin and skill for Agnes AI image and video generation. Provides
safe, configurable tools for text-to-image and text-to-video generation with
workspace isolation and retry logic.

## Quick Start

1. Clone this repository
2. Set `AGNES_API_KEY` environment variable
3. Deploy as a Hermes Agent plugin or skill

## Project Structure

```
agnes-media-skill/
├── plugins/
│   └── agnes_router/           # Hermes Agent plugin (tool handlers)
│       ├── __init__.py         # Tool registration
│       ├── plugin.yaml         # Plugin manifest + configurable parameters
│       ├── schemas.py          # Tool parameter schemas
│       ├── tools.py            # Image/video generation handlers
│       └── workspace_manager.py # Path validation + security
├── skills/
│   └── creative/
│       └── agnes-media/        # Hermes Agent skill
│           ├── SKILL.md        # Skill documentation
│           ├── scripts/
│           │   └── check_task.py    # Video task status checker
│           └── references/
│               └── video-async-guide.md  # Async video workflow guide
├── examples/                   # Example prompts and configurations
├── README.md                   # This file
├── LICENSE
└── .gitignore
```

## Features

- **Secure workspace isolation** — all generated files saved under a configurable
  workspace root with path traversal protection
- **Automatic retry** — transient errors (timeout, 503, rate limit) are retried
  with exponential backoff
- **Async video support** — video generation is handled correctly with polling
  and cron-based notification patterns
- **Environment configurable** — every parameter (endpoints, timeouts, models,
  workspace root) can be overridden via environment variables
- **Cron-safe** — works in scheduled jobs with automatic API key extraction

## Configuration

### Environment Variables

All variables are optional except `AGNES_API_KEY`.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AGNES_API_KEY` | string | **(required)** | Agnes AI API key |
| `AGNES_IMAGE_MODEL` | string | `agnes-image-2.0-flash` | Image generation model |
| `AGNES_VIDEO_MODEL` | string | `agnes-video-v2.0` | Video generation model |
| `AGNES_IMAGE_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/images/generations` | Image API endpoint |
| `AGNES_VIDEO_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/videos` | Video API endpoint |
| `AGNES_WORKSPACE_ROOT` | path | `~/workspace` | Root directory for media |
| `AGNES_IMAGE_TIMEOUT` | int | `180` | Image request timeout (seconds) |
| `AGNES_VIDEO_TIMEOUT` | int | `300` | Video submission timeout (seconds) |
| `AGNES_DOWNLOAD_TIMEOUT` | int | `300` | Media download timeout (seconds) |
| `AGNES_MAX_RETRIES` | int | `2` | Max retry attempts on transient errors |
| `AGNES_RETRY_DELAY` | float | `3.0` | Delay between retries (seconds) |

### Plugin YAML Configuration

The `plugins/agnes_router/plugin.yaml` file defines additional configuration
options that can be set in the Hermes Agent config:

```yaml
plugins:
  entries:
    agnes_router:
      workspace_root: /data/media        # Override default workspace
      image_endpoint: https://...        # Custom API endpoint
      video_endpoint: https://...        # Custom API endpoint
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 2
      retry_delay: 3.0
```

## Deployment

### Option 1: Hermes Agent Plugin (Recommended)

1. Copy the `plugins/agnes_router` directory to your Hermes Agent plugins path:

   ```bash
   cp -r plugins/agnes_router ~/.hermes/profiles/chat_01/plugins/
   ```

2. Enable the plugin in `config.yaml`:

   ```yaml
   plugins:
     enabled:
       - agnes_router
   ```

3. Set the API key:

   ```bash
   export AGNES_API_KEY="sk-your-key-here"
   ```

4. Restart Hermes Agent.

### Option 2: Hermes Agent Skill

1. Copy the `skills/creative/agnes-media` directory to your skills path:

   ```bash
   cp -r skills/creative/agnes-media ~/.hermes/profiles/chat_01/skills/creative/
   ```

2. The skill documents the tool usage patterns and best practices.
   The actual tool handlers come from the plugin (Option 1).

### Option 3: Standalone Script Usage

Use `check_task.py` independently:

```bash
python3 skills/creative/agnes-media/scripts/check_task.py task_abc123
```

## Tool Reference

### generate_image_via_pic01

Generates an image from a text prompt.

**Parameters:**

| Param | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Project slug (ASCII only, no slashes) |
| `prompt` | Yes | string | — | Detailed visual description |
| `file_name` | Yes | string | — | Output filename with extension |
| `size` | No | string | `1024x1024` | Image dimensions (WIDTHxHEIGHT) |

**Output:** Image saved to `<workspace>/<project>/images/<file_name>`

### generate_video_via_mov01

Generates a video from a text prompt.

**Parameters:**

| Param | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Project slug (ASCII only, no slashes) |
| `prompt` | Yes | string | — | Detailed video/storyboard description |
| `file_name` | Yes | string | — | Output filename with extension |

**Output:** Video saved to `<workspace>/<project>/videos/<file_name>`

**Note:** Video generation is async. The tool returns immediately with a task ID.
Use `check_task.py` or direct API polling to check completion status.

## Security & Operational Guidelines

### Agent Identity

You are the master controller agent responsible for daily conversation, document writing, information retrieval, project workspace management, and subordinate media task scheduling.

You have two subordinate specialized capability interfaces. Unless the user asks about architecture details, do not proactively expose internal codenames:

1. `generate_image_via_pic01` — Image generation service, specializing in text-to-image, image-to-image, and image modification. Underlying Agnes model: `agnes-image-2.0-flash`.
2. `generate_video_via_mov01` — Audio/video and video generation service, specializing in video, animation, and multimedia generation. Underlying Agnes model: `agnes-video-v2.0`.

### Workspace & Project Isolation Rules

1. All file read/write and media generation tasks must operate within a specific project directory.
2. The unified workspace root is `~/workspace` (configurable via `AGNES_WORKSPACE_ROOT`).
3. If the user has not explicitly specified a current project, you must ask or guide the user to define a compliant project name, e.g. `brand_retro`, `game_design`, `project_alpha`.
4. When calling subordinate media tools, you must accurately pass the current project name as `project_name` and propose a reasonable filename with the correct extension.
5. `project_name` must be a single directory slug — no `../`, slashes, backslashes, absolute paths, or any content attempting to escape the workspace.
6. Never attempt to construct out-of-bounds paths such as `/etc`, `../`, `~/.ssh`. Media tools confine files to `<workspace>/<project>/images` or `<workspace>/<project>/videos`.

### Interaction & Behavioral Norms

- Trigger media tools **only** when the user explicitly requests image, poster, illustration, visual design, video, animation, or multimedia generation.
- Handle text, search, document, code, and planning tasks yourself — do not invoke media tools for these.
- On media tool success, report the local file path to the user; if the tool returns a `remote_url`, display it alongside.
- On media tool failure, clearly report the cause. If a security block occurred, state directly that the path request was blocked.
- By default only `chat_01` is active; `pic_01` and `mov_01` are internal/debug profiles — do not start gateways for them externally.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ok: false` with async message | Video queued | Poll task status |
| `ok: false` with `security_blocked` | Invalid project/filename | Use ASCII-only slugs |
| `ok: false` with HTTP error | API returned error | Check logs, retry |
| `ok: false` with connection error | Network issue | Retry (automatic) |
| `ok: false` with "无效的令牌" | Bad API key | Check AGNES_API_KEY |

## Maintenance

### Updating the Plugin

1. Edit files in `plugins/agnes_router/`
2. Restart Hermes Agent to pick up changes
3. Test with a simple image generation

### Updating the Skill

1. Edit `skills/creative/agnes-media/SKILL.md`
2. Update version number in frontmatter
3. Commit changes

### Troubleshooting

1. **API key not working**: Verify `AGNES_API_KEY` is set and not a literal string
2. **Videos never complete**: Check task status via `check_task.py`
3. **Path errors**: Ensure project_name contains only ASCII letters, digits, `-`, `_`
4. **Rate limits**: Increase `AGNES_MAX_RETRIES` or `AGNES_RETRY_DELAY`
5. **Timeouts**: Increase `AGNES_IMAGE_TIMEOUT` or `AGNES_VIDEO_TIMEOUT`

## License

MIT License — see LICENSE file.

## Compatibility

- Python 3.9+
- Hermes Agent (any version supporting plugins and skills)
- Linux, macOS, Windows
- Agnes AI API (apihub.agnes-ai.com)
