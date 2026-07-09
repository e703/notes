# Agnes Media Kit

> **Agnes AI 文生图 · 图生图 · 视频生成 — 命令行工具包**
>
> 基于 [Agnes AI](https://agnes-ai.com) API (agnes-image-2.0-flash & agnes-video-v2.0) 的纯 CLI 工具箱，支持批量处理、队列重试、异步轮询。可独立部署或作为外部技能导入。

---

## 特性

- **三种图片模式**: 文生图 / 图生图 / 多图合成
- **三种视频模式**: 文生视频 / 图生视频 (Ti2Vid) / 关键帧动画
- **队列感知重试**: 遇 503 Queue Full 自动串行重试
- **异步轮询**: 视频生成异步提交 + 定时轮询完成
- **批量处理**: JSON 驱动批量图片生成
- **安全设计**: 无硬编码密钥、路径校验、工作目录隔离
- **可import**: 脚本均可作为 `skill_view()` 或外部工具的导入源

---

## 快速开始

### 前置依赖

- Python 3.10+
- 标准库 (urllib, json, base64, argparse) — 无需第三方包
- [Agnes AI API Key](https://agnes-ai.com) — 注册获取

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/agnes-media-kit.git
cd agnes-media-kit

# 2. 配置 API 密钥
cp config/.env.example .env
# 编辑 .env 填入 AGNES_API_KEY
source .env

# 或直接 export
export AGNES_API_KEY="sk-xxxxxxxx"
```

### 快速测试

```bash
# 文生图
python3 scripts/generate_image.py --project test --prompt "A cute cat on white background" --output cat.png

# 文生视频
python3 scripts/generate_video.py --project test --prompt "A cat walking on beach at sunset" --output cat.mp4

# 查看结果
ls ~/workspace/test/target/images/
ls ~/workspace/test/target/videos/
```

---

## 配置

### 环境变量 (优先级最高)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGNES_API_KEY` | — | **必需**。Agnes AI API 密钥 |
| `AGNES_IMAGE_MODEL` | `agnes-image-2.0-flash` | 图片模型 ID |
| `AGNES_VIDEO_MODEL` | `agnes-video-v2.0` | 视频模型 ID |
| `AGNES_API_BASE` | `https://apihub.agnes-ai.com` | API 地址 |
| `AGNES_IMAGE_TIMEOUT` | `180` | 图片请求超时 (秒) |
| `AGNES_VIDEO_TIMEOUT` | `300` | 视频请求超时 (秒) |
| `AGNES_POLL_INTERVAL` | `30` | 视频轮询间隔 (秒) |
| `AGNES_MAX_POLLS` | `60` | 最大轮询次数 |
| `AGNES_MAX_RETRIES` | `10` | 图片重试次数 |
| `AGNES_RETRY_DELAY` | `30` | 重试间隔 (秒) |
| `AGNES_WORKSPACE_ROOT` | `~/workspace` | 输出根目录 |

### 配置文件 (config.yaml)

参见 `config/config.example.yaml`。支持通过 YAML 配置文件设置默认参数。

### 硬编码位置 (优先级最低)

各个脚本内置常量（`DEFAULT_MODEL`、`DEFAULT_TIMEOUT` 等）。修改源代码中的常量会改变默认行为。

---

## 参数参考

### 文生图 / 图生图 — `scripts/generate_image.py`

| 参数 | 短名 | 类型 | 必需 | 默认 | 说明 |
|------|------|------|------|------|------|
| `--project` | `-p` | string | 是 | — | 项目目录名 (ASCII slug) |
| `--prompt` | `-P` | string | 是 | — | 图像描述 (建议 ≥30 字符) |
| `--output` | `-o` | string | 是 | — | 输出文件名 (如 `cat.png`) |
| `--size` | `-s` | string | 否 | `1024x1024` | 格式 `WIDTHxHEIGHT` |
| `--ref-url` | — | string[] | 否 | — | 参考图 URL (可多次指定) |
| `--ref-image` | — | string[] | 否 | — | 本地参考图路径 (可多次，自动转 data URI) |
| `--retries` | — | int | 否 | env/10 | 最大重试次数 |
| `--retry-delay` | — | int | 否 | env/30 | 重试间隔 (秒) |
| `--timeout` | — | int | 否 | env/180 | 请求超时 (秒) |
| `--dry-run` | — | flag | 否 | — | 仅打印请求体 |
| `--verbose` | `-v` | flag | 否 | — | 详细输出 |

#### 使用示例

```bash
# 文生图
python3 scripts/generate_image.py --project my_project --prompt "A cat on white" --output cat.png

# 图生图 (URL 参考)
python3 scripts/generate_image.py --project my_project --prompt "Transform to anime" \
    --ref-url https://example.com/cat.jpg --output cat_anime.png

# 图生图 (本地文件)
python3 scripts/generate_image.py --project my_project --prompt "Add sunglasses" \
    --ref-image sources/images/cat.jpg --output cat_cool.png

# 多图合成
python3 scripts/generate_image.py --project my_project --prompt "Merge into battle scene" \
    --ref-url https://example.com/hero.png --ref-url https://example.com/dragon.png \
    --output battle.png

# 自定义尺寸 + verbose
python3 scripts/generate_image.py -p my_project -P "Pixel art cat" -o cat_pixel.png \
    -s 768x768 -v

# 仅查看请求体 (不发送)
python3 scripts/generate_image.py -p test -P "test" -o test.png --dry-run
```

### 文生视频 / 图生视频 — `scripts/generate_video.py`

| 参数 | 短名 | 类型 | 必需 | 默认 | 说明 |
|------|------|------|------|------|------|
| `--project` | `-p` | string | 是 | — | 项目目录名 |
| `--prompt` | `-P` | string | 是 | — | 视频描述 |
| `--output` | `-o` | string | 是 | — | 输出文件名 (如 `intro.mp4`) |
| `--width` | — | int | 否 | `1152` | 宽度 |
| `--height` | — | int | 否 | `768` | 高度 |
| `--num-frames` | — | int | 否 | `121` | 总帧数 (8n+1: 81/121/241/441) |
| `--frame-rate` | — | int | 否 | `24` | 帧率 (1-60) |
| `--seed` | — | int | 否 | 随机 | 随机种子 |
| `--negative-prompt` | — | string | 否 | — | 负面描述 |
| `--steps` | — | int | 否 | 8 | 推理步数 |
| `--ref-image` | — | string | 互斥 | — | 本地参考图 (Ti2Vid) |
| `--ref-url` | — | string | 互斥 | — | 参考图 URL (Ti2Vid) |
| `--keyframes` | — | flag | 否 | — | 关键帧动画模式 |
| `--keyframe-urls` | — | string[] | 否 | — | 额外关键帧 URL |
| `--no-wait` | — | flag | 否 | — | 提交后不等待 (保存 task_id) |
| `--poll-interval` | — | int | 否 | env/30 | 轮询间隔 (秒) |
| `--max-polls` | — | int | 否 | env/60 | 最大轮询 |
| `--timeout` | — | int | 否 | env/300 | 请求超时 (秒) |
| `--dry-run` | — | flag | 否 | — | 仅打印请求体 |
| `--verbose` | `-v` | flag | 否 | — | 详细输出 |

#### 使用示例

```bash
# 文生视频 (121帧 ≈ 5秒)
python3 scripts/generate_video.py --project my_project --prompt "A cat walking on beach" \
    --output beach_cat.mp4

# 图生视频 (Ti2Vid)
python3 scripts/generate_video.py --project my_project --prompt "Cat starts skateboarding" \
    --ref-image sources/images/cat.jpg --output skateboard.mp4

# 更长视频 (241帧 ≈ 10秒)
python3 scripts/generate_video.py -p my_project -P "Sunset landscape, time-lapse" \
    -o sunset.mp4 --num-frames 241 --frame-rate 24

# 关键帧动画
python3 scripts/generate_video.py -p my_project -P "Smooth morphing" \
    --ref-url https://example.com/f1.jpg \
    --keyframe-urls https://example.com/f2.jpg https://example.com/f3.jpg \
    --keyframes --output animation.mp4

# 提交后离开 (稍后查询)
python3 scripts/generate_video.py -p my_project -P "Cat video" -o cat.mp4 --no-wait
# 稍后查询:
python3 scripts/check_task.py <video_id_从_task_info.json>

# 种子固定以确保可复现
python3 scripts/generate_video.py -p test -P "Flowing particles" -o particles.mp4 --seed 42
```

### 任务查询 — `scripts/check_task.py`

| 参数 | 短名 | 说明 |
|------|------|------|
| `video_id` | — | 视频 ID (原始或 base64 编码均可) |
| `--watch` | `-w` | 持续轮询直到完成 |
| `--interval` | `-i` | 轮询间隔 (默认 30s) |
| `--max-polls` | — | 最大轮询次数 (默认 60) |
| `--raw` | — | 输出原始 JSON |
| `--download` | `-d` | 完成后下载到指定路径 |

```bash
# 查询一次
python3 scripts/check_task.py video_d39354f7...

# 持续轮询
python3 scripts/check_task.py --watch video_d39354f7...

# 轮询并下载
python3 scripts/check_task.py --watch video_d39354f7... --download output.mp4

# 原始 JSON 输出
python3 scripts/check_task.py --raw video_d39354f7...
```

### 批量处理 — `scripts/batch_generate.py`

```bash
# 使用 JSON 任务文件
python3 scripts/batch_generate.py --tasks tasks.json

# 或编辑脚本中的 TASKS 列表直接运行
python3 scripts/batch_generate.py

# 覆盖重试参数
python3 scripts/batch_generate.py --tasks tasks.json --max-attempts 20 --retry-delay 15
```

**tasks.json 格式**:
```json
[
  {
    "prompt": "A cat on white background, studio lighting",
    "output": "target/images/cat_01.jpg",
    "size": "1024x1024"
  },
  {
    "prompt": "Transform to anime style",
    "output": "target/images/cat_02.jpg",
    "ref_image": "sources/images/ref_cat.jpg"
  }
]
```

---

## 项目结构

```
agnes-media-kit/
├── README.md                  # 本文件 — 主文档
├── SECURITY.md                # 安全规范
├── LICENSE                    # MIT 许可证
├── .gitignore                 # Git 忽略规则
│
├── config/
│   ├── config.example.yaml    # 配置模板 (参考用)
│   └── .env.example           # 环境变量模板
│
├── scripts/
│   ├── generate_image.py      # 文生图 / 图生图 / 多图合成
│   ├── generate_video.py      # 文生视频 / 图生视频 / 关键帧
│   ├── check_task.py          # 视频任务状态查询
│   └── batch_generate.py      # 批量图片生成
│
├── templates/
│   └── image-queue-retry.py   # 单图队列重试模板
│
├── references/
│   ├── image-api-guide.md     # 图片 API 完整参考
│   ├── video-api-guide.md     # 视频 API 完整参考
│   └── prompt-templates.md    # Prompt 工程模板
│
└── tests/
    └── (待编写测试用例)
```

### 输出目录 (自动创建)

```
~/workspace/<project_name>/
├── sources/
│   ├── images/         # 输入 - 原始图片
│   ├── videos/         # 输入 - 原始视频
│   ├── scripts/        # 输入 - 项目脚本
│   └── others/         # 输入 - 其他文件
└── target/
    ├── images/         # 输出 - 生成的图片
    ├── videos/         # 输出 - 生成的视频
    ├── scripts/        # 输出 - 生成脚本/日志
    └── others/         # 输出 - 其他 (任务信息 JSON)
```

---

## 安全规范

详见 [SECURITY.md](SECURITY.md)，核心要点：

1. **API 密钥** — 仅通过环境变量注入，绝不硬编码
2. **路径隔离** — project slug 严格校验，拒绝 `/../` 等路径穿越
3. **文件上传** — 优先使用 Data URI 而非 HTTP URL 传输参考图
4. **Git 安全** — `.env` 已在 `.gitignore`，密钥不会被提交
5. **日志安全** — 不打印 API key，错误信息截断

---

## 部署方式

### 方式 1: 独立 CLI 使用

```bash
git clone https://github.com/YOUR_USERNAME/agnes-media-kit.git
export AGNES_API_KEY="sk-xxx"
cd agnes-media-kit
python3 scripts/generate_image.py -p my_project -P "Hello world" -o hello.png
```

### 方式 2: 作为外部技能导入 (Hermes Agent / 其他 Agent 框架)

在 Hermes Agent 中，通过 `skill_view()` 导入脚本内容，或通过插件系统挂载目录：

```yaml
# config.yaml — 挂载为自定义技能源
skills:
  paths:
    - /path/to/agnes-media-kit/scripts
```

或在其他工具中直接调用:

```python
import subprocess
result = subprocess.run(
    ["python3", "/path/to/agnes-media-kit/scripts/generate_image.py",
     "--project", "my_project",
     "--prompt", "A cat",
     "--output", "cat.png"],
    env={"AGNES_API_KEY": "sk-xxx"},
    capture_output=True
)
```

### 方式 3: 作为 Python 模块导入

```python
# 将 scripts/ 目录加入 sys.path 后直接 import 函数
import sys, json
sys.path.insert(0, "/path/to/agnes-media-kit/scripts")

# 调用内部函数 (需确保 AGNES_API_KEY 已设置)
# 注意: 脚本设计为 CLI 入口，内部函数可复用但无独立 API 稳定性保证
```

---

## 发布到 GitHub

```bash
# 1. 创建 GitHub 仓库 (不要勾选 README / LICENSE / .gitignore)
# 2. 本地操作
cd ~/workspace/agnes-media-kit
git init
git add .
git commit -m "Initial release: Agnes Media Kit"

# 3. 添加 remote
git remote add origin https://github.com/YOUR_USERNAME/agnes-media-kit.git
git push -u origin main
```

### 发布前检查清单

- [ ] 确认 `AGNES_API_KEY` 无硬编码 (`git grep "sk-"`)
- [ ] 确认 `.env` 已加入 `.gitignore`
- [ ] 确认 `config.yaml` 示例中使用 `"${AGNES_API_KEY}"` 占位符
- [ ] 确认 LICENSE 文件存在
- [ ] 运行所有脚本检查语法 (`python3 -m py_compile scripts/*.py`)
- [ ] 确认 README.md 中的 GitHub URL 更新为实际仓库地址

---

## 常见问题

### Q: 图片生成返回 503
A: API 队列满了。脚本会自动重试（最多 10 次，间隔 30 秒）。如果频繁遇到，降低请求频率。

### Q: 视频查询一直返回 processing
A: 视频推理通常需要 ~90 秒。如果超过 5 分钟仍未完成，可能是任务失败。使用 `--raw` 查看原始响应，检查 `error` 字段。

### Q: 下载得到的是 XML 文件而非视频/图片
A: URL 可能已过期或无效。重新查询视频状态获取最新 URL。

### Q: 如何固定随机种子？
A: 视频生成使用 `--seed 42`；图片生成目前不支持种子固定。

### Q: num_frames 有哪些有效值？
A: 必须是 8n+1: 81 (≈3.4s @24fps), 121 (≈5s), 241 (≈10s), 441 (≈18s)。最大值 441。

---

## License

[MIT](LICENSE) © 2026 Agnes Media Kit Contributors

---

## 致谢

- [Agnes AI](https://agnes-ai.com) — 提供图像与视频生成 API
- [Nous Research](https://nousresearch.com) — Hermes Agent 框架