# 安全规范 — Agnes Media Kit

## 核心原则

1. **绝不硬编码 API 密钥**
2. **绝不将凭据提交到 Git 仓库**
3. **工作目录隔离，防止路径穿越**
4. **最小日志原则，避免凭据泄露**

---

## 1. API 密钥管理

### ✅ 正确做法
```bash
# 通过环境变量注入
export AGNES_API_KEY="sk-xxxxx"

# 或使用 .env 文件（已加入 .gitignore）
cp config/.env.example .env
# 编辑 .env 填入密钥
source .env
```

### ❌ 错误做法
```python
# 绝不这样做！
api_key = "sk-xxxxx"  # 硬编码在源代码中
```

### 生产环境
- 使用密钥管理服务（如 GitHub Secrets、Vault、AWS Secrets Manager）
- CI/CD 中通过环境变量注入，而非配置文件
- 定期轮换密钥

---

## 2. 防止路径穿越

所有脚本对 `--project` 和 `--output` 参数进行严格校验：

```python
# 允许的字符：字母、数字、连字符、下划线
project = "my_project"  # ✅
project = "../../etc"  # ❌ 拒绝

# 文件名：ASCII 字符，无路径分隔符
output = "cat.png"  # ✅
output = "../../etc/passwd"  # ❌ 拒绝
```

### 输出路径规则
- `--project` 必须是 ASCII 安全 slug（仅字母、数字、`-`、`_`）
- `--output` 必须是纯文件名，不含路径分隔符
- 所有输出都在 `$AGNES_WORKSPACE_ROOT/<project>/target/` 内

---

## 3. 日志安全

- **不要**在日志中打印 `AGNES_API_KEY`
- 脚本中 API key 仅用于 `Authorization` header，不记录
- 错误响应中的 API key 自动截断（最长 200 字符）

---

## 4. 文件安全

### 项目文件隔离
```
~/workspace/<project>/
├── sources/           # 输入文件（原始图片）
│   ├── images/
│   ├── videos/
│   └── others/
├── target/            # 输出文件（生成内容）
│   ├── images/
│   ├── videos/
│   └── others/
└── scripts/           # 项目级脚本
```

### 不要将以下文件提交到 Git
- `.env` 文件（含 API 密钥）
- 生成的图片/视频（除非明确需要）
- `__pycache__/` 目录
- 日志文件

---

## 5. 网络请求安全

- 所有 API 请求使用 HTTPS 加密
- 图片输入优先使用 **Data URI** 而非 HTTP URL（避免中间人攻击）
- 下载文件时验证内容类型（拒绝非视频/图片的 XML 错误响应）

---

## 6. 清单 — 发布前检查

- [ ] 源代码中无硬编码密钥（`grep -r "sk-" .`）
- [ ] `.env` 已加入 `.gitignore`
- [ ] 所有凭据通过环境变量读取
- [ ] 配置文件示例中使用 `"${AGNES_API_KEY}"` 占位符
- [ ] 路径参数经过安全校验
- [ ] 日志中不包含敏感信息