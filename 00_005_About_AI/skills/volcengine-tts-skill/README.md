# 火山引擎 TTS 配音技能

使用火山引擎（字节跳动）TTS API 将文字转为语音 MP3，使用用户自己的克隆音色。

## 目录结构

```
volcengine-tts-skill/
├── SKILL.md        # Hermes Agent 技能文件（可直接注册使用）
├── tts.sh          # 独立可执行脚本（不依赖 Hermes）
├── README.md       # 部署说明
```

## 快速部署（在其他机器上）

### 1. 安装 Hermes Agent

参考 [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs) 安装。

### 2. 注册技能

```bash
# 将 SKILL.md 复制到 Hermes 技能目录
cp SKILL.md ~/.hermes/profiles/<profile_name>/skills/voice/volcengine-tts/SKILL.md
```

### 3. 配置 API Key 和音色 ID

编辑 `~/.hermes/profiles/<profile_name>/.env`，追加：

```bash
VOLC_TTS_API_KEY=你的API_KEY
VOLC_TTS_VOICE_ID=你的克隆音色ID
```

### 4. 确认网络

该 API 需要通过 `openspeech.bytedance.com` 访问，国内网络正常，海外可能因 SSL 问题无法连接。

---

## 独立使用（不依赖 Hermes）

如果不需要 Hermes，直接运行 `tts.sh`：

```bash
# 1. 先配置环境变量
export VOLC_TTS_API_KEY="你的API_KEY"
export VOLC_TTS_VOICE_ID="你的克隆音色ID"

# 2. 运行脚本朗读文字
./tts.sh "要朗读的文字" output.mp3
```

## 参数说明

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| voice_type | 克隆音色 ID | S_1CIdRxxxx | 来自 .env |
| encoding | 音频编码格式 | wav / pcm / mp3 / ogg_opus | mp3 |
| speed_ratio | 语速 | 0.1 ~ 2.0 | 1.0 |
| pitch_ratio | 音调 | 0.1 ~ 3.0 | 1.0 |
| volume_ratio | 音量 | 0.1 ~ 3.0 | 1.0 |
| rate | 采样率 | 8000 / 16000 / 24000 | 24000 |
| split_sentence | 复刻音色语速优化 | 0 / 1 | 0 |

## 注意事项

- API 返回 JSON，音频数据在 `data` 字段（Base64 编码），需要通过管道解码
- 文字内容较长时，API 有 60s 超时限制，建议分段生成
- 海外网络可能无法连接（SSL_ERROR_SYSCALL），需在国内网络环境运行
