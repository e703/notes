# Agnes Media Skill

Hermes Agent 插件和技能包，用于 Agnes AI 图像和视频生成。提供安全、可配置的文本生成图像和文本生成视频工具，具备工作区隔离和自动重试机制。

## 快速开始

1. 克隆本仓库
2. 设置 `AGNES_API_KEY` 环境变量
3. 作为 Hermes Agent 插件或技能部署

## 项目结构

```
agnes-media-skill/
├── plugins/
│   └── agnes_router/           # Hermes Agent 插件（工具处理器）
│       ├── __init__.py         # 工具注册
│       ├── plugin.yaml         # 插件清单 + 可配置参数
│       ├── schemas.py          # 工具参数 Schema
│       ├── tools.py            # 图像/视频生成处理器
│       └── workspace_manager.py # 路径验证 + 安全校验
├── skills/
│   └── creative/
│       └── agnes-media/        # Hermes Agent 技能
│           ├── SKILL.md        # 技能文档
│           ├── scripts/
│           │   └── check_task.py    # 视频任务状态检查器
│           └── references/
│               └── video-async-guide.md  # 异步视频工作流指南
├── examples/                   # 示例提示词和配置
├── README.md                   # 英文文档
├── README_CN.md                # 本文档
├── LICENSE
└── .gitignore
```

## 功能特性

- **安全的工作区隔离** — 所有生成的文件保存在可配置的工作区根目录下，带有路径遍历保护
- **自动重试机制** — 瞬态错误（超时、503、限速）会自动重试，采用指数退避策略
- **异步视频支持** — 正确处理视频生成的异步行为，支持轮询和基于 cron 的通知
- **全环境变量可配置** — 每个参数（端点、超时时间、模型、工作区根目录）均可通过环境变量覆盖
- **Cron 安全** — 在定时任务中正常工作，自动处理 API key 提取

## 配置

### 环境变量

除 `AGNES_API_KEY` 外，其余均为可选。

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `AGNES_API_KEY` | string | **必填** | Agnes AI API 密钥 |
| `AGNES_IMAGE_MODEL` | string | `agnes-image-2.0-flash` | 图像生成模型 |
| `AGNES_VIDEO_MODEL` | string | `agnes-video-v2.0` | 视频生成模型 |
| `AGNES_IMAGE_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/images/generations` | 图像 API 端点 |
| `AGNES_VIDEO_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/videos` | 视频 API 端点 |
| `AGNES_WORKSPACE_ROOT` | path | `~/workspace` | 媒体输出根目录 |
| `AGNES_IMAGE_TIMEOUT` | int | `180` | 图像请求超时时间（秒） |
| `AGNES_VIDEO_TIMEOUT` | int | `300` | 视频提交超时时间（秒） |
| `AGNES_DOWNLOAD_TIMEOUT` | int | `300` | 媒体下载超时时间（秒） |
| `AGNES_MAX_RETRIES` | int | `2` | 瞬态错误的最大重试次数 |
| `AGNES_RETRY_DELAY` | float | `3.0` | 重试间隔（秒） |

### 插件 YAML 配置

`plugins/agnes_router/plugin.yaml` 定义了可在 Hermes Agent 配置中设置的额外参数：

```yaml
plugins:
  entries:
    agnes_router:
      workspace_root: /data/media        # 覆盖默认工作区
      image_endpoint: https://...        # 自定义 API 端点
      video_endpoint: https://...        # 自定义 API 端点
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 2
      retry_delay: 3.0
```

## 部署方式

### 方式一：Hermes Agent 插件（推荐）

1. 将 `plugins/agnes_router` 目录复制到 Hermes Agent 插件路径：

   ```bash
   cp -r plugins/agnes_router ~/.hermes/profiles/chat_01/plugins/
   ```

2. 在 `config.yaml` 中启用插件：

   ```yaml
   plugins:
     enabled:
       - agnes_router
   ```

3. 设置 API 密钥：

   ```bash
   export AGNES_API_KEY="sk-你的密钥"
   ```

4. 重启 Hermes Agent。

### 方式二：Hermes Agent 技能

1. 将 `skills/creative/agnes-media` 目录复制到技能路径：

   ```bash
   cp -r skills/creative/agnes-media ~/.hermes/profiles/chat_01/skills/creative/
   ```

2. 该技能文档化了工具的使用模式和最佳实践。实际的工具处理器来自插件（方式一）。

### 方式三：独立脚本使用

独立使用 `check_task.py`：

```bash
python3 skills/creative/agnes-media/scripts/check_task.py task_abc123
```

## 工具参考

### generate_image_via_pic01

从文本提示生成图像。

**参数：**

| 参数 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_name` | 是 | string | — | 项目标识（仅限 ASCII，不含斜杠） |
| `prompt` | 是 | string | — | 详细的视觉描述 |
| `file_name` | 是 | string | — | 带扩展名的输出文件名 |
| `size` | 否 | string | `1024x1024` | 图像尺寸（宽x高） |

**输出：** 图像保存到 `<workspace>/<project>/images/<file_name>`

### generate_video_via_mov01

从文本提示生成视频。

**参数：**

| 参数 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_name` | 是 | string | — | 项目标识（仅限 ASCII，不含斜杠） |
| `prompt` | 是 | string | — | 详细的视频/分镜描述 |
| `file_name` | 是 | string | — | 带扩展名的输出文件名 |

**输出：** 视频保存到 `<workspace>/<project>/videos/<file_name>`

**注意：** 视频生成是异步的。工具会立即返回任务 ID。请使用 `check_task.py` 或直接查询 API 来检查完成状态。

## 安全与行为规范

### 主控 Agent 身份

你是主控 Agent，负责所有的日常对话交互、文档编写、信息检索、项目空间管理和下级媒体任务调度。

你拥有两个下级专用能力接口。除非用户询问架构细节，否则不需要主动暴露内部代号：

1. `generate_image_via_pic01` — 图像生成服务，专职文生图、图生图、图像修改。底层 Agnes 模型为 `agnes-image-2.0-flash`。
2. `generate_video_via_mov01` — 音视频/视频生成服务，专职视频、动画和多媒体生成。底层 Agnes 模型为 `agnes-video-v2.0`。

### 工作空间与项目隔离准则

1. 所有文件写入、读取和媒体生成任务，必须在一个具体项目目录下进行。
2. 统一工作空间根目录是 `~/workspace`（可通过 `AGNES_WORKSPACE_ROOT` 配置）。
3. 如果用户没有显式指定当前项目，必须先询问或引导用户定义一个合规项目名，例如 `brand_retro`、`game_design`、`project_alpha`。
4. 调用下级媒体工具时，必须准确传入当前项目名 `project_name`，并拟定合理文件名，包含正确后缀名。
5. `project_name` 只能是单个目录名，不得包含 `../`、斜杠、反斜杠、绝对路径或任何试图跳出 workspace 的内容。
6. 绝对不要尝试构造 `/etc`、`../`、`~/.ssh` 等越界路径。媒体工具会把文件限制在 `<workspace>/<project>/images` 或 `<workspace>/<project>/videos`。

### 交互与行为规范

- 只有当用户明确提出图像、海报、插画、视觉设计、视频、动画或多媒体生成诉求时，才触发对应媒体工具。
- 文本、检索、文档、代码、规划等普通任务由你自己处理，不调用媒体工具。
- 媒体工具成功后，在最终回复中告知用户本地保存路径；如果工具返回 `remote_url`，也可同时展示远程 URL。
- 媒体工具失败时，清楚报告失败原因。若是安全拦截，直接说明该路径请求被拦截。
- 默认对外只运行 `chat_01`；`pic_01` 和 `mov_01` 是内部/备用调试 profile，不对外启动 gateway。

## 错误处理

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `ok: false` 附带异步消息 | 视频已排队 | 轮询任务状态 |
| `ok: false` 附带 `security_blocked` | 无效的项目/文件名 | 使用纯 ASCII 标识 |
| `ok: false` 附带 HTTP 错误 | API 返回错误 | 检查日志，重试 |
| `ok: false` 附带连接错误 | 网络问题 | 重试（自动） |
| `ok: false` 附带 "无效的令牌" | API 密钥错误 | 检查 AGNES_API_KEY |

## 维护

### 更新插件

1. 编辑 `plugins/agnes_router/` 中的文件
2. 重启 Hermes Agent 以应用更改
3. 使用简单的图像生成进行测试

### 更新技能

1. 编辑 `skills/creative/agnes-media/SKILL.md`
2. 更新 frontmatter 中的版本号
3. 提交更改

### 故障排查

1. **API 密钥不工作**：验证 `AGNES_API_KEY` 已设置且不是字面量字符串
2. **视频一直未完成**：通过 `check_task.py` 检查任务状态
3. **路径错误**：确保 project_name 仅包含 ASCII 字母、数字、`-`、`_`
4. **限速**：增加 `AGNES_MAX_RETRIES` 或 `AGNES_RETRY_DELAY`
5. **超时**：增加 `AGNES_IMAGE_TIMEOUT` 或 `AGNES_VIDEO_TIMEOUT`

## 许可证

MIT 许可证 — 详见 LICENSE 文件。

## 兼容性

- Python 3.9+
- Hermes Agent（支持插件和技能的任意版本）
- Linux、macOS、Windows
- Agnes AI API（apihub.agnes-ai.com）
