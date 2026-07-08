#!/bin/bash
# 火山引擎 TTS 独立脚本（不依赖 Hermes Agent）
# 用法: ./tts.sh "要朗读的文字" [输出文件名.mp3]
#
# 前置条件: 设置环境变量 VOLC_TTS_API_KEY 和 VOLC_TTS_VOICE_ID
#
# 示例:
#   export VOLC_TTS_API_KEY="your_key_here"
#   export VOLC_TTS_VOICE_ID="your_voice_id_here"
#   ./tts.sh "你好，世界" hello.mp3

set -e

TEXT="${1:?错误: 请提供要朗读的文字}"
OUTPUT="${2:-output.mp3}"
REQID="TTS_$(date +%s)_$(shuf -i 1000-9999 -n 1)"

: "${VOLC_TTS_API_KEY:?错误: 请设置 VOLC_TTS_API_KEY 环境变量}"
: "${VOLC_TTS_VOICE_ID:?错误: 请设置 VOLC_TTS_VOICE_ID 环境变量}"

echo "📢 正在合成语音..."
echo "   输出: $OUTPUT"
echo "   长度: ${#TEXT} 字"

curl -s -X POST 'https://openspeech.bytedance.com/api/v1/tts' \
  -H "x-api-key: $VOLC_TTS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "app": { "cluster": "volcano_icl" },
    "user": { "uid": "豆包语音" },
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
    print(f'✅ 成功!')
    print(f'   大小: {len(audio)/1024:.1f} KB')
    print(f'   时长: {int(data[\"addition\"][\"duration\"])/1000:.1f} 秒')
else:
    print(f'❌ 失败: {data[\"message\"]} (code: {data[\"code\"]})')
    sys.exit(1)
"
