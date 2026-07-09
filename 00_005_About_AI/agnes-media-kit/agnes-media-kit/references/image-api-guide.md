# Agnes Image API v2.0 — 完整参考

## 端点

```
POST https://apihub.agnes-ai.com/v1/images/generations
Authorization: Bearer ${AGNES_API_KEY}
Content-Type: application/json
```

## 三种工作流

### 1. 文生图 (Text-to-Image)

```json
{
  "model": "agnes-image-2.0-flash",
  "prompt": "A silver tabby cat sitting on a minimalist white background, soft studio lighting...",
  "size": "1024x1024",
  "extra_body": {
    "response_format": "url"
  }
}
```

### 2. 图生图 (Image-to-Image) — 单参考图

```json
{
  "model": "agnes-image-2.0-flash",
  "prompt": "Transform into a cyberpunk night scene with neon lights",
  "size": "1024x1024",
  "extra_body": {
    "response_format": "url",
    "image": ["data:image/jpeg;base64,/9j/4AAQ..."]
  }
}
```

### 3. 多图合成 (Multi-Image Composition) — 多参考图

```json
{
  "model": "agnes-image-2.0-flash",
  "prompt": "Merge these characters into a single action scene, fighting a dragon",
  "size": "1024x1024",
  "extra_body": {
    "response_format": "url",
    "image": [
      "data:image/png;base64,iVBOR...",
      "data:image/png;base64,iVBOR..."
    ]
  }
}
```

## 参数说明

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `model` | 顶层 | string | 是 | 模型 ID。当前: `agnes-image-2.0-flash` |
| `prompt` | 顶层 | string | 是 | 图像描述或编辑指令。建议 ≥30 字符 |
| `size` | 顶层 | string | 是 | 格式: `WIDTHxHEIGHT`。常见: `1024x1024`, `768x768` |
| `extra_body.response_format` | 嵌套 | string | 否 | `"url"`（默认）或 `"b64_json"` |
| `extra_body.image` | 嵌套 | string[] | 否 | 参考图数组。每项为 data URI 或 HTTP URL |

## 输入图像格式

- **Data URI 格式**: `data:<mime>;base64,<base64_encoded>`
- **支持 MIME**: `image/jpeg`, `image/png`, `image/webp`, `image/gif`, `image/bmp`
- **URL 格式**: 也支持公开的 HTTP(S) 图片链接
- **最大尺寸**: 建议每张图 ≤ 20MB base64 编码后

## 响应格式

成功 (200/201):
```json
{
  "created": 1234567890,
  "data": [
    {
      "url": "https://apihub.agnes-ai.com/...",
      "revised_prompt": "(optional) Auto-improved prompt text"
    }
  ]
}
```

固定参数：
- 响应始终在 `data[0].url` 包含下载链接
- `revised_prompt` 可选，仅当 API 优化了你的 prompt

## 错误处理

### 503 Queue Full
```json
{
  "error": {
    "message": "image queue is full, please retry later",
    "type": "server_error",
    "param": null,
    "code": null
  }
}
```
**处理策略**：
- 串行重试（不要并行请求）
- 每次重试间隔 30 秒
- 最大 10-15 次尝试
- 参见 `scripts/batch_generate.py` 实现

### 其他错误码
- `400` — 参数错误（检查 prompt/size/格式）
- `401` — API key 无效
- `429` — 速率限制（减少频率）
- `500` — 服务端错误（重试）

## 提示工程指南

参考文件: `references/prompt-templates.md`

- 建议描述 ≥30 个字符
- 风格词放在句首: `"Anime style, ..."`, `"Photorealistic, ..."`
- 图生图时 prompt 描述转换效果而非重新描述
- 中文 prompt 也支持，但英文效果通常更好