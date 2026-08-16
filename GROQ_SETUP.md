# 🚀 Groq API 免费层申请指南

Groq 提供免费的 Llama 模型 API，速度极快，非常适合文档问答应用。

## 步骤 1：注册 Groq 账号

1. 访问 [console.groq.com](https://console.groq.com)
2. 点击 **"Sign Up"** 或 **"Login"**
3. 使用 Google/GitHub 账号或邮箱注册

## 步骤 2：获取 API Key

1. 登录后，进入 [API Keys 页面](https://console.groq.com/keys)
2. 点击 **"Create API Key"**
3. 输入名称（如 `pdf-qa-app`）
4. 复制生成的 API Key（格式：`gsk_xxxx...`）

⚠️ **重要**：API Key 只显示一次，请妥善保存！

## 步骤 3：免费层限额

Groq 免费层（December 2024）：

| 模型 | 限制 |
|------|------|
| `llama-3.1-8b-instant` | 30 RPM, 14,400 RPD |
| `llama-3.1-70b-versatile` | 30 RPM, 14,400 RPD |
| `llama-3.2-11b-vision-preview` | 30 RPM, 14,400 RPD |
| `llama-3.2-90b-vision-preview` | 30 RPM, 14,400 RPD |
| `mixtral-8x7b-32768` | 30 RPM, 14,400 RPD |

RPM = Requests Per Minute（每分钟请求数）
RPD = Requests Per Day（每天请求数）

免费层足够个人使用和小规模演示。

## 步骤 4：配置应用

### 本地运行（环境变量）

```bash
export LLM_MODE=groq
export GROQ_API_KEY=gsk_your_key_here
export GROQ_MODEL=llama-3.1-8b-instant
streamlit run app.py
```

### Streamlit Cloud（Secrets）

在 Streamlit Cloud 应用的 Secrets 中添加：
```toml
LLM_MODE = "groq"
GROQ_API_KEY = "gsk_..."
GROQ_MODEL = "llama-3.1-8b-instant"
```

## 步骤 5：测试

```python
from qa_engine import QAEngine
engine = QAEngine()
print(f"模式: {engine.mode}")
print(f"连接: {'✓' if engine.check_connection() else '✗'}")
```

## ⚠️ 注意事项

1. **免费层限制**：每天 14,400 次请求，个人使用足够
2. **速率限制**：每分钟 30 次请求，避免并发过多
3. **商业化**：Groq 免费层不可转售，如需商业化请升级付费计划
4. **数据隐私**：你的文档内容会发送到 Groq API，请阅读 [Groq 隐私政策](https://groq.com/privacy-policy/)

## 💡 推荐模型

| 用途 | 模型 | 说明 |
|------|------|------|
| **快速问答** | `llama-3.1-8b-instant` | 速度快，适合简单问答 |
| **复杂分析** | `llama-3.1-70b-versatile` | 质量高，速度稍慢 |
| **多模态** | `llama-3.2-11b-vision-preview` | 支持图片输入 |

## 🔄 切换模型

随时可以更改 `GROQ_MODEL` 环境变量或 Secrets 中的值来切换模型。

## 📊 成本估算

免费层：
- 文档问答：每次 ~1,000 tokens
- 免费额度：每天 14,400 次请求
- 成本：**$0**

付费层（按量计费）：
- 价格：约 $0.59 / 1M tokens (输入) + $0.79 / 1M tokens (输出)
- 典型使用：个人用户每月几美元

---

## 本地 + Groq 双模式

应用支持同时配置本地 Ollama 和云端 Groq：

- **本地模式**（`LLM_MODE=ollama`）：完全免费，数据不上传
- **云端模式**（`LLM_MODE=groq`）：随时随地访问，有免费额度

根据你的需求切换模式即可！