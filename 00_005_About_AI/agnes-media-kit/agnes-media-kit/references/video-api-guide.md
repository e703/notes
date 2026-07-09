# Agnes Video API v2.0 — 完整参考

## 端点

### 提交任务
```
POST https://apihub.agnes-ai.com/v1/videos
Authorization: Bearer ${AGNES_API_KEY}
Content-Type: application/json
```

### 查询状态 (❌ 不是 `/v1/videos/{task_id}`)
```
GET https://apihub.agnes-ai.com/agnesapi?video_id=<real_video_id>
Authorization: Bearer ${AGNES_API_KEY}
```

> ⚠️ **关键陷阱**: 恰好有两个不同的端点。`GET /v1/videos/{task_id}` 会返回 404。必须使用 `/agnesapi?video_id=<real_video_id>`。而且 POST 返回的 `video_id` 是 base64 编码的，需要解码才能获取真实的 video_id。

---

## 三种模式

### 1. 文生视频 (Text-to-Video)

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "A cat walking on a tropical beach at sunset, cinematic quality...",
  "width": 1152,
  "height": 768,
  "num_frames": 121,
  "frame_rate": 24
}
```

### 2. 图生视频 Ti2Vid (Image-to-Video)

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "The cat starts skateboarding down a hill with wheels spinning",
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "width": 1152,
  "height": 768,
  "num_frames": 121,
  "frame_rate": 24
}
```

### 3. 关键帧动画 (Keyframe Animation)

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "Smooth transition between frames",
  "width": 1152,
  "height": 768,
  "num_frames": 241,
  "frame_rate": 24,
  "extra_body": {
    "mode": "keyframes",
    "image": [
      "https://example.com/frame1.jpg",
      "https://example.com/frame2.jpg",
      "https://example.com/frame3.jpg"
    ]
  }
}
```

> 关键帧模式下 `image` 放在 `extra_body` 内（数组）；Ti2Vid 模式下 `image` 是顶层字段（字符串）。

---

## 参数说明

| 参数 | 位置 | 类型 | 默认值 | 必填 | 说明 |
|------|------|------|--------|------|------|
| `model` | 顶层 | string | — | 是 | 模型 ID: `agnes-video-v2.0` |
| `prompt` | 顶层 | string | — | 是 | 视频内容描述。建议 ≥40 字符 |
| `width` | 顶层 | int | 1152 | 否 | 视频宽度（会被映射到最近的有效分辨率） |
| `height` | 顶层 | int | 768 | 否 | 视频高度 |
| `num_frames` | 顶层 | int | 121 | 否 | 总帧数。必须为 8n+1。允许值: 81, 121, 241, 441 |
| `frame_rate` | 顶层 | int | 24 | 否 | 帧率 (1-60) |
| `seed` | 顶层 | int | 随机 | 否 | 随机种子，用于可复现结果 |
| `negative_prompt` | 顶层 | string | — | 否 | 描述要避免的内容 |
| `num_inference_steps` | 顶层 | int | 8 | 否 | 推理步数 |

### 参考图参数

| 模式 | 字段 | 位置 | 类型 | 说明 |
|------|------|------|------|------|
| Ti2Vid | `image` | **顶层** | string | 单张 data URI 或 URL |
| Keyframes | `image` | `extra_body.image` | string[] | 多张图片数组 |

---

## 分辨率映射

请求的尺寸会被映射到最接近的可用分辨率：

| 请求尺寸区间 | 映射结果 |
|-------------|---------|
| ~1152x768 | 1088x832 (720p 4:3) |
| ~1400x768 | (下一档) |
| ~768x1152 | 垂直模式对应 |

检查响应中的 `size_mapping`:
```json
"size_mapping": {
  "adjusted": true,
  "requested_width": 1152,
  "requested_height": 768,
  "width": 1088,
  "height": 832,
  "resolution": "720p",
  "ratio": "4:3"
}
```

---

## 视频 ID 解码

POST 返回的 `video_id` 是 base64 编码的，包含元数据：

```
Raw: video_Zmx...bGk=
Decoded: litellm:custom_llm_provider:openai;model_id:agnes-video-v2.0;video_id:video_d39354f7...
                                      └───────────────── 真实 video_id ─────────────────┘
```

解码流程：
1. 去掉 `video_` 前缀
2. Base64 解码
3. 用正则 `video_id:(\S+)` 提取真实 ID

---

## 响应格式

### 提交成功
```json
{
  "task_id": "...",
  "video_id": "video_Zmx...bGk="
}
```

### 查询完成
```json
{
  "status": "completed",
  "progress": 100,
  "id": "video_d39354f7...",
  "url": "https://apihub.agnes-ai.com/video_d39354f7_20260709.mp4",
  "seconds": "5.04",
  "size": "1088x832",
  "perf_infer_s": 87.25,
  "size_mapping": { "adjusted": true, ... }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `status` | `completed` / `processing` / `failed` |
| `progress` | 0-100 百分比 |
| `id` | 真实视频 ID |
| `url` | 下载链接（完成时有） |
| `seconds` | 视频时长 |
| `size` | 实际分辨率 |
| `perf_infer_s` | 推理耗时（秒） |
| `internal_status` | 内部状态（调试用） |
| `internal_progress` | 内部进度（调试用） |

---

## 错误处理

- **提交 401**: API key 无效或缺失
- **提交 400**: 参数错误（检查 num_frames 是否为 8n+1）
- **查询 404**: video_id 无效或使用了错误端点
- **下载 NoSuchKey (127 字节 XML)**: 视频文件尚未就绪或已过期

---

## 性能基准

| 指标 | 典型值 |
|------|--------|
| 推理时间 | ~87 秒 |
| 总等待时间 | ~2 分钟 |
| 121 帧 @ 24fps | ~5 秒视频 |
| 241 帧 @ 24fps | ~10 秒视频 |