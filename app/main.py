# app/main.py

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.llm_client import (
    chat,
    LLMAuthError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMError,
)

app = FastAPI(title="Job Copilot API", version="0.1.0")  # 初始化 FastAPI 应用

# ── 内存会话存储 ─────────────────────────────────────────
"""
会话存储字典，用于维护用户与助手的对话历史

类型结构：
- 外层 dict：键为会话ID（字符串类型），值为该会话的消息列表
- 内层 list[dict]：按时间顺序存储的消息列表，每个消息是一个字典

消息字典结构：
- role: 角色（如 "user" 表示用户，"assistant" 表示助手）
- content: 消息内容

示例结构：
{
    "session_id_1": [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮助你的？"}
    ],
    "session_id_2": [
        {"role": "user", "content": "帮我写一份简历"}
    ]
}
"""
sessions: dict[str, list[dict]] = {}

MAX_HISTORY_ROUNDS = 10
SYSTEM_PROMPT = "你是一个简洁、友好的 AI 助手。"


# ── 请求 / 响应模型 ──────────────────────────────────────
class ChatRequest(BaseModel):
    provider: str = Field(default="deepseek", description="模型提供方")
    model: str = Field(default="deepseek-v3", description="模型名称")
    session_id: Optional[str] = Field(  # Optional指定可选None类型,Field指定默认值和描述
        default=None, description="会话 ID，为空则自动创建"
    )
    message: str = Field(..., description="用户消息")


class ChatResponse(BaseModel):
    reply: str
    usage: dict
    provider: str
    model: str
    session_id: str
    request_id: str  # 请求ID，用于唯一标识每次请求


# ── 工具函数 ─────────────────────────────────────────────
def trim_history(history: list[dict]) -> list[dict]:
    max_messages = MAX_HISTORY_ROUNDS * 2
    if len(history) > max_messages:
        history = history[-max_messages:]
    return history


# ── 路由 ─────────────────────────────────────────────────
@app.get(
    "/"
)  # 根路由，用于检查服务是否运行。当客户端向服务器的根路径 / 发送 HTTP GET 请求时，会触发 root() 函数。
def root():
    return {"status": "ok", "message": "Job Copilot API is running"}


@app.post(
    "/chat", response_model=ChatResponse
)  # 聊天路由，用于处理用户消息并返回助手回复。
def chat_endpoint(req: ChatRequest):  # 创建一个实例req，用于存储用户请求的参数
    # session_id 不存在则自动创建一个新会话
    session_id = req.session_id or str(
        uuid.uuid4()
    )  # 如果请求中提供了 session_id，就使用它；否则，生成一个新的唯一标识符（UUID）作为 session_id。

    logger.info(
        f"请求开始 | session={session_id} | provider={req.provider} | model={req.model}"
    )  # 记录请求开始时间、会话ID、提供模型提供方和模型名称

    if session_id not in sessions:
        sessions[session_id] = []  # 如果会话不存在，就创建一个新的空列表作为会话历史。

    # 处理用户消息
    history = sessions[session_id]  # 获取当前会话的历史记录。
    history.append({"role": "user", "content": req.message})  # 将用户消息添加到对话历史
    history = trim_history(history)  # 裁剪历史，保留最近 N 轮对话

    # 构建消息列表 = 系统提示 + 对话历史
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:  # 调用 LLM 客户端获取助手回复
        result = chat(
            provider=req.provider,
            model=req.model,
            messages=messages,
        )
    # 处理异常情况
    except LLMAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 处理助手回复
    history.append({"role": "assistant", "content": result.text})
    sessions[session_id] = history

    logger.info(
        f"请求结束 | session={session_id} | tokens={result.usage['total_tokens']} | latency={result.raw_meta['latency_ms']}ms"
    )  # 记录请求结束时间、会话ID、总token数和耗时

    # 返回助手回复
    return ChatResponse(
        reply=result.text,
        usage=result.usage,
        provider=result.raw_meta["provider"],
        model=result.raw_meta["model"],
        session_id=session_id,
        request_id=str(uuid.uuid4()),  # 生成一个新的唯一标识符（UUID）作为请求ID。
    )


# 清除会话路由
@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "ok", "message": f"会话 {session_id} 已清除"}
    raise HTTPException(status_code=404, detail="会话不存在")
