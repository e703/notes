---
name: volcengine-tts
description: 使用火山引擎（字节跳动）TTS API 生成语音，使用用户自己的克隆音色
category: voice
---

# 火山引擎 TTS 配音

使用 火山引擎 TTS API 将文字转为语音 MP3，使用用户自己的克隆音色。

## 前置条件

- API Key 和 Voice ID 保存在 `~/.hermes/profiles/<profile_name>/.env` 文件中，格式：
  ```
  VOLC_TTS_API_KEY=your_api_key
  VOLC_TTS_VOICE_ID=your_voice_id
  ```
- 需要在能访问 `openspeech.bytedance.com` 的网络环境下运行（国内网络）

## 技能用法

⚠️ 每次开始前，先展示当前配置和默认参数，等用户确认后再执行。

### 生成语音文件

```bash
# 从 .env 加载配置
set -a; source ~/.hermes/profiles/<profile_name>/.env; set +a

TEXT="要朗读的文字内容"
OUTPUT="output.mp3"
REQID="$(date +%s)$(shuf -i 1000-9999 -n 1)"

# 请求并解码 Base64 音频数据
curl -s -X POST 'https://openspeech.bytedance.com/api/v1/tts' \
  -H "x-api-key: $VOLC_TTS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "app": {
        "cluster": "volcano_icl"
    },
    "user": {
        "uid": "豆包语音"
    },
    "audio": {
        "voice_type": "'"$VOLC_TTS_VOICE_ID"'",
        "encoding": "mp3",
        "speed_ratio": 1.0
    },
    "request": {
        "reqid": "'"$REQID"'",
        "text": "'"$TEXT"'",
        "operation": "query"
    }
}' | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
if data['code'] == 3000:
    audio = base64.b64decode(data['data'])
    with open('$OUTPUT', 'wb') as f:
        f.write(audio)
    print(f'✓ 已生成: $OUTPUT')
    print(f'  大小: {len(audio)/1024:.1f} KB')
    print(f'  时长: {int(data[\"addition\"][\"duration\"])/1000:.1f} 秒')
else:
    print(f'✗ 失败: {data[\"message\"]} (code: {data[\"code\"]})')
"
```

### 调节语速/音调示例

```bash
set -a; source ~/.hermes/profiles/<profile_name>/.env; set +a

TEXT="要朗读的文字内容"
OUTPUT="output_slow.mp3"
REQID="$(date +%s)$(shuf -i 1000-9999 -n 1)"

curl -s -X POST 'https://openspeech.bytedance.com/api/v1/tts' \
  -H "x-api-key: $VOLC_TTS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "app": { "cluster": "volcano_icl" },
    "user": { "uid": "豆包语音" },
    "audio": {
        "voice_type": "'"$VOLC_TTS_VOICE_ID"'",
        "encoding": "mp3",
        "speed_ratio": 0.8,
        "pitch_ratio": 1.0,
        "volume_ratio": 1.0
    },
    "request": {
        "reqid": "'"$REQID"'",
        "text": "'"$TEXT"'",
        "operation": "query"
    }
}' | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
if data['code'] == 3000:
    audio = base64.b64decode(data['data'])
    with open('$OUTPUT', 'wb') as f: f.write(audio)
    print(f'✓ {len(audio)/1024:.1f} KB, {int(data[\"addition\"][\"duration\"])/1000:.1f}s')
else:
    print(f'✗ {data[\"message\"]}')
"
```

## 参数说明

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| voice_type | 克隆音色 ID | 来自 .env | — |
| encoding | 音频编码格式 | wav / pcm / mp3 / ogg_opus | pcm |
| speed_ratio | 语速 | 0.1 ~ 2.0 | 1.0 |
| pitch_ratio | 音调 | 0.1 ~ 3.0 | 1.0 |
| volume_ratio | 音量 | 0.1 ~ 3.0 | 1.0 |
| rate | 采样率 | 8000 / 16000 / 24000 | 24000 |
| split_sentence | 复刻音色语速优化 | 0 / 1 | 0 |

## 注意事项

- API 返回 JSON，音频数据在 `data` 字段（Base64 编码），需要通过管道解码
- 文字的 UTF-8 编码长度建议控制在 1024 字节以内，复刻音色无此限制但有 60s HTTP 超时
- 该 API 在国内网络环境下运行正常，海外可能因 SSL 问题无法连接

## 常见坑点

- **❌ 不要用 `-o` 直接保存：** API 返回的是 JSON，不是 MP3 二进制。`curl ... -o output.mp3` 会把 JSON 文本写进 MP3 文件，播放器无法识别。必须通过 `python3` 解码 `data` 字段。
- **❌ 不要硬编码 Key：** API Key 和 Voice ID 保存在 `.env` 文件中，不要写在脚本或代码里。
- **❌ 不要忽略 `set -a`：** 用 `source .env` 前必须 `set -a`，否则变量不会 export 到子进程。
- **⚠️ V1 API 已标记不推荐：** 火山引擎推荐使用 V3 接口（`/api/v3/tts/unidirectional`），后续可迁移。
