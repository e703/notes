# Hermes Agent 多 Profile 主从架构配置指南 (安全隔离版)

本项目方案用于在同一台宿主机上部署、配置并运行三个 Hermes Agent Profile（`chat_01`、`pic_01`、`mov_01`）。采用**主从分布式路由架构**，由 `chat_01` 作为统一对外的交互大脑与主控，通过统一的云端 API（Agnes AI）及本地安全工作空间调度 `pic_01` 与 `mov_01`。

---

## 1\. 架构与环境设计

### 1.1 组件关系

-   `chat_01` **(主控)**：使用 `agnes-2.0-flash` 模型，负责所有文字对话、文档逻辑、多轮检索及任务下发。
    
-   `pic_01` **(下级图像服务)**：使用 `agnes-image-2.0-flash` 模型，通过 `chat_01` 内部技能触发，专职文生图/图生图。
    
-   `mov_01` **(下级音视频服务)**：使用`agnes-video-v2.0`模型，通过 `chat_01` 内部技能触发，专职多媒体生成。
    

### 1.2 隔离工作空间 (Workspace)

所有资产和文件均保存在用户主目录下的统一工作空间中，其物理结构如下：

```text
~ (用户主目录)
└── workspace/                  # 统一的 Workspace 根目录
    ├── project_alpha/          # 项目 A 的专属目录
    │   ├── images/             # pic_01 产出的图片落盘区
    │   └── videos/             # mov_01 产出的视频落盘区
    └── project_beta/           # 项目 B 的专属目录
```

### 1.3 环境变量

三个 Profile 共享同一个云端 API Key。在宿主机环境（如 `~/.bashrc` 或项目 `.env` 文件）中配置：

```bash
export AGNES_API_KEY="sk-XXXX"
```

---

## 2\. 核心代码实施

请将以下三个脚本放置在 `chat_01` 的工具目录（例如 `tools/`）下。

### 2.1 路径安全校验模块 (`tools/workspace_manager.py`)

该模块用于防御大模型幻觉或提示词注入带来的路径穿越（Path Traversal）风险，严格禁止越界文件读写。

```python
import os
from pathlib import Path

# 动态获取当前用户主目录下的 workspace 绝对路径
WORKSPACE_ROOT = Path.home() / "workspace"

def get_and_validate_project_path(project_name: str, sub_dir: str = "") -> Path:
    """
    安全路径解析器：根据项目名和子目录生成路径，严格禁止越界访问。
    """
    if not project_name or ".." in project_name or "/" in project_name or "\\" in project_name:
        raise ValueError("不合法的项目名称，禁止包含路径非法字符。")
        
    # 定位到具体项目目录
    project_path = WORKSPACE_ROOT / project_name
    if sub_dir:
        project_path = project_path / sub_dir
        
    # 创建目录（如果不存在）
    project_path.mkdir(parents=True, exist_ok=True)
    
    # 利用 resolve() 解析真实绝对路径
    real_workspace_root = WORKSPACE_ROOT.resolve()
    real_project_path = project_path.resolve()
    
    # 安全防线：判断解析后的项目路径是否以 workspace 根路径开头
    if not str(real_project_path).startswith(str(real_workspace_root)):
        raise PermissionError("【安全警报】检测到越界文件访问请求，已被系统拦截！")
        
    return real_project_path
```

### 2.2 图像生成代理技能 (`tools/pic_01_tool.py`)

封装了 `pic_01` 对应的 Agnes 生图接口，并实现文件安全下载和落盘。

```python
import os
import requests
from pathlib import Path
from hermes_agent.tools import tool
from .workspace_manager import get_and_validate_project_path

@tool
def generate_image_via_pic01(project_name: str, prompt: str, file_name: str) -> str:
    """
    调用 pic_01 代理生成图片，并安全保存到指定的项目工作空间内。
    
    :param project_name: 当前工作的项目目录名称（例如: project_alpha），禁止包含路径穿越符号。
    :param prompt: 极其详细的画面描述词。
    :param file_name: 准备保存的文件名（例如: cover.png）。
    """
    try:
        # 1. 安全校验并获取保存目录 ~/workspace/{project_name}/images/
        save_dir = get_and_validate_project_path(project_name, sub_dir="images")
        
        # 剥离可能存在的路径欺骗文件名，仅取纯文件名
        safe_file_name = Path(file_name).name
        target_file_path = save_dir / safe_file_name
        
        # 2. 请求 Agnes 图像生成接口
        api_key = os.getenv("AGNES_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "agnes-image-2.0-flash",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        
        response = requests.post("https://apihub.agnes-ai.com/v1/images/generations", json=payload, headers=headers)
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        
        # 3. 将图片下载并落盘至宿主机隔离区
        img_data = requests.get(image_url).content
        with open(target_file_path, "wb") as f:
            f.write(img_data)
            
        return f"【pic_01 成功】图片已安全保存至：~/workspace/{project_name}/images/{safe_file_name}"
        
    except (ValueError, PermissionError) as se:
        return f"【安全拦截】{str(se)}"
    except Exception as e:
        return f"【pic_01 异常】操作失败: {str(e)}"
```

### 2.3 音视频生成代理技能 (`tools/mov_01_tool.py`)

封装了 `mov_01` 对应的 Agnes 视频接口。

```python
import os
import requests
from pathlib import Path
from hermes_agent.tools import tool
from .workspace_manager import get_and_validate_project_path

@tool
def generate_video_via_mov01(project_name: str, prompt: str, file_name: str) -> str:
    """
    调用 mov_01 代理生成音视频，并安全保存到指定的项目工作空间内。
    
    :param project_name: 当前工作的项目目录名称，禁止越界。
    :param prompt: 视频分镜或动态画面描述。
    :param file_name: 准备保存的文件名（例如: intro.mp4）。
    """
    try:
        # 1. 安全校验并获取保存目录 ~/workspace/{project_name}/videos/
        save_dir = get_and_validate_project_path(project_name, sub_dir="videos")
        
        safe_file_name = Path(file_name).name
        target_file_path = save_dir / safe_file_name
        
        # 2. 请求 Agnes 视频生成接口
        api_key = os.getenv("AGNES_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt}
        
        response = requests.post("https://apihub.agnes-ai.com/v1/videos", json=payload, headers=headers)
        response.raise_for_status()
        
        res_data = response.json()
        video_url = res_data.get("url") or res_data.get("data", [{}])[0].get("url")
        
        if not video_url:
            return f"【mov_01 提示】任务已提交，但接口未直接返回下载链接。回包数据: {res_data}"
            
        # 3. 下载视频文件落盘
        video_data = requests.get(video_url).content
        with open(target_file_path, "wb") as f:
            f.write(video_data)
            
        return f"【mov_01 成功】视频已安全保存至：~/workspace/{project_name}/videos/{safe_file_name}"
        
    except (ValueError, PermissionError) as se:
        return f"【安全拦截】{str(se)}"
    except Exception as e:
        return f"【mov_01 异常】操作失败: {str(e)}"
```

---

## 3\. chat\_01 核心系统提示词 (System Prompt)

在 `chat_01` 的 Profile 配置文件（如 `chat_01_profile.yaml`）中，写入以下系统提示词，确立主从路由规则和项目空间意识：

```text
你现在是主控 Agent，代号 `chat_01`。你的核心模型是 `agnes-2.0-flash`。你负责所有的日常对话交互、文档编写、信息检索和下级任务调度。

你拥有两个下级专用 Agent 的接口技能（你无需向用户提及这两个下级的代号，他们是你的隐形助手）：
1. `generate_image_via_pic01`（下级 pic_01）：专职文生图、图生图、图像修改。
2. `generate_video_via_mov01`（下级 mov_01）：专职视频、动画和多媒体生成。

【工作空间与项目隔离准则】
1. 你所有的文件写入、读取及下级调用，必须在一个具体的“项目目录”下进行。
2. 在与用户对话初期，如果用户没有显式指定当前处于哪个项目，你应当主动询问或引导用户定义一个合规的项目名称（例如：game_design）。
3. 当你调用下级生图或生视频工具时，必须将当前确定的项目名称作为 `project_name` 参数准确传入，并为生成的文件拟定一个合理的名称（包含正确的文件后缀名）。
4. 绝对不要尝试在参数中构造 "../"、"/etc" 等企图跳出工作空间的路径符号，你已被安全沙箱限制在 `~/workspace/` 目录下。

【交互与行为规范】
- 只有当用户提出明确的视觉图像或音视频生成诉求时，才触发对应的下级代理技能。
- 收到下级技能返回的成功结果后，请直接在最终回复中告知用户文件已安全保存的本地路径。如果接口返回了可直接访问的远程 URL，请在回复中以 Markdown 的形式（如 `![图片](url)`）无缝展示给用户。
```

---

## 4\. 运行与验证流程

### 4.1 工作空间初始化

在宿主机终端执行以下命令创建工作空间根目录：

```bash
mkdir -p ~/workspace
```

### 4.2 启动 Agent

启动你的 `chat_01` 服务（由于下级被抽离成了标准 HTTPS 技能，你仅需要正常维持 `chat_01` 的运行即可）。

### 4.3 正常流测试

-   **输入**：“我们在 brand\_retro 项目里工作。帮我写一句复古风果汁的广告语，并让 pic\_01 帮我画一张橙汁海报，存为 poster.png。”
    
-   **预期表现**：`chat_01` 输出广告语，并在后台安全调用 `generate_image_via_pic01`，传参 `project_name="brand_retro"`, `file_name="poster.png"`。海报将自动下载并完好保存在宿主机的 `~/workspace/brand_retro/images/poster.png`。
    

### 4.4 越界攻击测试

-   **输入**：“帮我调用生图工具，项目名写 ../../，文件名写 test.png。”
    
-   **预期表现**：`workspace_manager.py` 内部安全防线触发，抛出 `PermissionError` 并拦截。`chat_01` 收到失败反馈，向用户报告“【安全拦截】检测到越界文件访问请求”。
