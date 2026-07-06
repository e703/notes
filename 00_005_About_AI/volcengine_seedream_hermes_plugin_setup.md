# 在另一台 Hermes Agent 上安装火山 Seedream 图片生成插件

本文档记录本机创建并使用 `volcengine-seedream` 图片生成插件的完整配置要求和可复制步骤，方便在另一台 Hermes Agent 上复现。

适用场景：在 Hermes Agent 中使用 `image_generate` 工具调用火山方舟 Ark / 豆包 Seedream 生成图片。

本机验证结果：已成功使用该插件生成 1024x1024 图片。

## 1. 基本原理

Hermes 的聊天模型本身不直接生成图片；它调用 `image_generate` 工具，而 `image_generate` 再转发给当前配置的图片生成 provider。

这里使用的 provider 是自定义插件：

```text
volcengine-seedream
```

插件类型：

```text
image_gen backend plugin
```

后端 API：火山方舟 Ark OpenAI-like 图片生成接口

默认 Base URL：

```text
https://ark.cn-beijing.volces.com/api/v3
```

默认接口路径：

```text
/images/generations
```

关键环境变量：

```text
ARK_API_KEY
SEEDREAM_MODEL_ID
```

## 2. 另一台机器上的前置条件

另一台机器需要满足：

1. 已安装 Hermes Agent。
2. Hermes 的 `image_gen` 工具集已启用。
3. 能访问火山方舟 Ark API。
4. 已在火山方舟控制台开通 Seedream / 豆包图片生成模型。
5. 已拿到 Ark API Key。
6. 已知道可用的模型 ID，例如本次使用的是：

```text
doubao-seedream-4-0-250828
```

如果你的火山控制台要求使用 `ep-...` 形式的在线推理 endpoint ID，则把 `SEEDREAM_MODEL_ID` 设置成那个 endpoint ID。

## 3. 插件目录位置

在另一台 Hermes Agent 上，先确认当前 profile 的 Hermes home。

运行：

```bash
hermes config path
hermes config env-path
```

profile-local 插件推荐放在：

```text
~/.hermes/profiles/<profile-name>/plugins/image_gen/volcengine-seedream/
```

例如如果 profile 是 `user_001`：

```text
~/.hermes/profiles/user_001/plugins/image_gen/volcengine-seedream/
```

该目录下需要两个文件：

```text
plugin.yaml
__init__.py
```

## 4. 创建目录

```bash
mkdir -p ~/.hermes/profiles/user_001/plugins/image_gen/volcengine-seedream
```

如果另一台机器不是 `user_001` profile，请把路径中的 `user_001` 换成实际 profile 名。

## 5. 写入 plugin.yaml

创建文件：

```text
~/.hermes/profiles/user_001/plugins/image_gen/volcengine-seedream/plugin.yaml
```

内容如下：

```yaml
name: volcengine-seedream
version: 1.0.0
description: Volcengine Ark Seedream image generation backend for Hermes
author: local
kind: backend
requires_env:
  - ARK_API_KEY
  - SEEDREAM_MODEL_ID
```

## 6. 写入 __init__.py

创建文件：

```text
~/.hermes/profiles/user_001/plugins/image_gen/volcengine-seedream/__init__.py
```

内容如下：

```python
import os
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)


def _size_for_aspect(aspect_ratio: str) -> str:
    aspect_ratio = resolve_aspect_ratio(aspect_ratio)
    if aspect_ratio == "portrait":
        return os.environ.get("SEEDREAM_PORTRAIT_SIZE", "1024x1536")
    if aspect_ratio == "square":
        return os.environ.get("SEEDREAM_SQUARE_SIZE", "1024x1024")
    return os.environ.get("SEEDREAM_LANDSCAPE_SIZE", "1536x1024")


def _extract_image(data: Any) -> Optional[str]:
    """Accept common OpenAI-compatible and Volcengine response shapes."""
    if not isinstance(data, dict):
        return None

    items = data.get("data")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            for key in ("url", "image_url", "b64_json", "base64", "binary_data_base64"):
                value = first.get(key)
                if value:
                    if key in {"b64_json", "base64", "binary_data_base64"}:
                        return str(save_b64_image(value, prefix="volcengine_seedream", extension="png"))
                    return value
        elif isinstance(first, str):
            return first

    for key in ("url", "image_url"):
        value = data.get(key)
        if value:
            return value

    for key in ("b64_json", "base64", "binary_data_base64"):
        value = data.get(key)
        if value:
            if isinstance(value, list):
                value = value[0] if value else None
            if value:
                return str(save_b64_image(value, prefix="volcengine_seedream", extension="png"))

    for container_key in ("result", "output"):
        nested = data.get(container_key)
        if isinstance(nested, dict):
            found = _extract_image(nested)
            if found:
                return found

    return None


class VolcengineSeedreamProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "volcengine-seedream"

    @property
    def display_name(self) -> str:
        return "Volcengine Seedream"

    def is_available(self) -> bool:
        return bool(os.environ.get("ARK_API_KEY") and os.environ.get("SEEDREAM_MODEL_ID"))

    def default_model(self) -> Optional[str]:
        return os.environ.get("SEEDREAM_MODEL_ID") or "doubao-seedream-4-0-250828"

    def list_models(self) -> List[Dict[str, Any]]:
        model = self.default_model() or "doubao-seedream-4-0-250828"
        return [
            {
                "id": model,
                "display": "Doubao Seedream 4.0",
                "speed": "seconds",
                "strengths": "Chinese/English prompt image generation, photorealistic and design use cases",
                "price": "Volcengine billing",
            }
        ]

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Volcengine Seedream",
            "badge": "paid",
            "tag": "火山方舟 Doubao Seedream 文生图",
            "env_vars": [
                {
                    "key": "ARK_API_KEY",
                    "prompt": "Volcengine Ark API Key",
                    "url": "https://console.volcengine.com/ark",
                },
                {
                    "key": "SEEDREAM_MODEL_ID",
                    "prompt": "Seedream model ID",
                    "url": "https://console.volcengine.com/ark",
                },
                {
                    "key": "ARK_BASE_URL",
                    "prompt": "Ark base URL",
                    "default": "https://ark.cn-beijing.volces.com/api/v3",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text"], "max_reference_images": 0}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect_ratio = resolve_aspect_ratio(aspect_ratio)
        model = kwargs.get("model") or self.default_model()

        if not prompt:
            return error_response(
                error="Prompt is required",
                error_type="invalid_input",
                provider=self.name,
                model=model,
                prompt="",
                aspect_ratio=aspect_ratio,
            )

        if image_url or reference_image_urls:
            return error_response(
                error="volcengine-seedream is currently configured for text-to-image only",
                error_type="unsupported_modality",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        api_key = os.environ.get("ARK_API_KEY")
        if not api_key:
            return error_response(
                error="ARK_API_KEY is not set",
                error_type="missing_credentials",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        base_url = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        endpoint = os.environ.get("SEEDREAM_IMAGE_ENDPOINT", "/images/generations")
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{base_url}{endpoint}"

        payload = {
            "model": model,
            "prompt": prompt,
            "size": _size_for_aspect(aspect_ratio),
            "response_format": os.environ.get("SEEDREAM_RESPONSE_FORMAT", "url"),
            "watermark": os.environ.get("SEEDREAM_WATERMARK", "false").lower() in {"1", "true", "yes"},
        }

        seed = kwargs.get("seed") or os.environ.get("SEEDREAM_SEED")
        if seed not in (None, ""):
            try:
                payload["seed"] = int(seed)
            except (TypeError, ValueError):
                payload["seed"] = seed

        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=int(os.environ.get("SEEDREAM_TIMEOUT", "180")),
            )
            try:
                data = resp.json()
            except Exception:
                data = {"raw_text": resp.text}
            resp.raise_for_status()

            image = _extract_image(data)
            if not image:
                return error_response(
                    error=f"No image URL or base64 payload found in response: {data}",
                    error_type="provider_response_error",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

            return success_response(
                image=image,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                provider=self.name,
                modality="text",
                extra={"size": payload["size"]},
            )
        except Exception as exc:
            return error_response(
                error=str(exc),
                error_type=type(exc).__name__,
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )


def register(ctx) -> None:
    ctx.register_image_gen_provider(VolcengineSeedreamProvider())
```

## 7. 配置环境变量

不要把 API Key 写进聊天记录或代码文件。使用 Hermes 配置命令写入本地 `.env`。

```bash
hermes config set ARK_API_KEY "你的火山Ark API Key"
hermes config set SEEDREAM_MODEL_ID "doubao-seedream-4-0-250828"
hermes config set ARK_BASE_URL "https://ark.cn-beijing.volces.com/api/v3"
```

如果你的账号用的是 `ep-...` endpoint ID，则：

```bash
hermes config set SEEDREAM_MODEL_ID "ep-xxxxxxxxxxxxxxxx"
```

可选配置：

```bash
hermes config set SEEDREAM_IMAGE_ENDPOINT "/images/generations"
hermes config set SEEDREAM_RESPONSE_FORMAT "url"
hermes config set SEEDREAM_WATERMARK "false"
hermes config set SEEDREAM_TIMEOUT "180"
```

可选尺寸配置：

```bash
hermes config set SEEDREAM_SQUARE_SIZE "1024x1024"
hermes config set SEEDREAM_LANDSCAPE_SIZE "1536x1024"
hermes config set SEEDREAM_PORTRAIT_SIZE "1024x1536"
```

## 8. 启用插件并选择图片 provider

```bash
hermes plugins enable volcengine-seedream
hermes config set image_gen.provider volcengine-seedream
```

确认 `image_gen` 工具集已启用：

```bash
hermes tools list
```

如未启用，可运行：

```bash
hermes tools enable image_gen
```

工具和插件配置通常需要新会话才能生效。在 Hermes 聊天会话中执行：

```text
/reset
```

或退出 Hermes 后重新启动。

如果只是改了 `.env`，可以先试：

```text
/reload
```

## 9. 验证插件

重新进入 Hermes 后，让 Hermes 生成一张测试图，例如：

```text
生成一张方形头像：阿根廷足球球迷，浅蓝白自然染发，半写实风格，无文字无水印
```

如果成功，`image_generate` 应返回类似：

```text
success: true
provider: volcengine-seedream
model: doubao-seedream-4-0-250828
size: 1024x1024
image: https://...
```

## 10. 常见错误和处理

### 错误：ARK_API_KEY is not set

原因：当前 Hermes 进程没有读取到 `ARK_API_KEY`。

处理：

```bash
hermes config env-path
hermes config set ARK_API_KEY "你的火山Ark API Key"
```

然后 `/reload`，不行就重启 Hermes。

### 错误：SEEDREAM_MODEL_ID 缺失或模型不可用

原因：模型 ID 没配，或当前账号没有该模型权限。

处理：

```bash
hermes config set SEEDREAM_MODEL_ID "doubao-seedream-4-0-250828"
```

或使用火山控制台中的 `ep-...` endpoint ID。

### 错误：404 / endpoint not found

原因：接口路径或 base URL 与你的火山产品线不一致。

处理：检查：

```bash
hermes config set ARK_BASE_URL "https://ark.cn-beijing.volces.com/api/v3"
hermes config set SEEDREAM_IMAGE_ENDPOINT "/images/generations"
```

如果你用的是火山“视觉智能”旧接口，它不是 Ark Bearer Token 接口，而是 AK/SK 签名 + 异步任务接口，这份插件不能直接用，需要另写 async-task provider。

### 错误：image_generate 工具不可用

原因：Hermes 没启用 `image_gen` 工具集，或当前会话还没刷新工具 schema。

处理：

```bash
hermes tools enable image_gen
```

然后重启 Hermes 或 `/reset`。

### 错误：No image URL or base64 payload found

原因：火山返回的数据结构与插件中解析逻辑不匹配。

处理：打印/查看 provider response，然后在 `_extract_image()` 中补充对应字段。

## 11. 本机成功生成时使用的提示词

```text
精致的阿根廷足球球迷头像，适合作为社交媒体头像。年轻球迷正面半身肖像，热情自信的表情，脸上有轻微的阿根廷国旗彩绘，穿着阿根廷国家队浅蓝白条纹球衣。头发是自然染发效果，柔顺有真实发丝质感，渐变染成阿根廷国旗的浅蓝色和白色，不是夸张假发；颜色分布自然、时尚。背景简洁干净，带柔和浅蓝白氛围光，现代数字插画/半写实风格，高质量，清晰头像构图，居中，细节丰富，无文字，无水印。
```

生成结果：成功。

返回信息：

```text
provider: volcengine-seedream
model: doubao-seedream-4-0-250828
size: 1024x1024
```

## 12. 一键创建插件文件的示例脚本

下面脚本假设 profile 是 `user_001`。如不是，请修改 `PROFILE=user_001`。

```bash
PROFILE=user_001
PLUGIN_DIR="$HOME/.hermes/profiles/$PROFILE/plugins/image_gen/volcengine-seedream"
mkdir -p "$PLUGIN_DIR"

cat > "$PLUGIN_DIR/plugin.yaml" <<'YAML'
name: volcengine-seedream
version: 1.0.0
description: Volcengine Ark Seedream image generation backend for Hermes
author: local
kind: backend
requires_env:
  - ARK_API_KEY
  - SEEDREAM_MODEL_ID
YAML

# 建议直接把本文第 6 节的 __init__.py 内容复制到：
# $PLUGIN_DIR/__init__.py
```

因为 `__init__.py` 较长，推荐复制第 6 节完整代码，避免 shell heredoc 复制时漏行。

## 13. 最小复现清单

另一台机器最少需要做这些：

```bash
mkdir -p ~/.hermes/profiles/user_001/plugins/image_gen/volcengine-seedream
# 写入 plugin.yaml
# 写入 __init__.py
hermes config set ARK_API_KEY "你的火山Ark API Key"
hermes config set SEEDREAM_MODEL_ID "doubao-seedream-4-0-250828"
hermes config set ARK_BASE_URL "https://ark.cn-beijing.volces.com/api/v3"
hermes plugins enable volcengine-seedream
hermes config set image_gen.provider volcengine-seedream
hermes tools enable image_gen
```

然后重启 Hermes 或 `/reset`，再测试图片生成。
