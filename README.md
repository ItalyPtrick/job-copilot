# Job Copilot — Week 1 后端基座

多模型 LLM 调用底座，支持 OpenAI 与 DeepSeek 切换，
提供 CLI 多轮对话与 FastAPI HTTP 接口。

## 环境要求
- Python 3.11+
- Conda

## 安装步骤

1. 克隆项目
   git clone https://github.com/ItalyPatrick/job-copilot.git
   cd job-copilot

2. 创建 Conda 环境
   conda create -n job_copilot python=3.11 -y
   conda activate job_copilot

3. 安装依赖
   pip install openai python-dotenv fastapi uvicorn httpx

4. 配置密钥
   cp .env.example .env
   # 用编辑器打开 .env，填入真实密钥

## 启动服务

uvicorn app.main:app --reload

访问 http://127.0.0.1:8000/docs 打开 Swagger 界面。

## 接口说明

### POST /chat
发送消息，支持多轮会话。

请求示例：
{
  "provider": "deepseek",
  "model": "deepseek-v3",
  "session_id": "可选，为空则自动创建",
  "message": "你好"
}

响应示例：
{
  "reply": "你好！很高兴见到你，有什么可以帮你的吗？😊",
  "usage": {
    "prompt_tokens": 24,
    "completion_tokens": 26,
    "total_tokens": 50
  },
  "provider": "deepseek",
  "model": "deepseek-v3",
  "session_id": "1",
  "request_id": "e8a9a7d2-e570-4252-8d15-f807e277eab7"
}

### DELETE /session/{session_id}
清除指定会话的历史记录。

## CLI 多轮对话

conda activate job_copilot
python scripts/cli_chat.py

可用命令：/clear /history /exit /help

## 常见错误排查

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| 401 AuthenticationError | 密钥错误 | 检查 .env 里的 API Key |
| 504 超时 | 网络问题或 BASE_URL 错误 | 检查 DEEPSEEK_BASE_URL / OPENAI_BASE_URL |
| model not found | 模型名拼错 | DeepSeek 用 deepseek-v3，OpenAI 用 gpt-4o-mini |
| sessions 重启后消失 | 会话存储在内存中 | 已知局限，后续版本引入数据库 |

## 支持的模型

| Provider | 模型名 | 说明 |
|----------|--------|------|
| deepseek | deepseek-v3 | 默认 |
| deepseek | deepseek-r1 | 推理增强版 |
| openai | gpt-4o-mini | 备用，通过中转访问 |