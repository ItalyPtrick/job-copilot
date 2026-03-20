"""
目标：建立单一入口，后续业务层只依赖一个方法。
执行：封装 chat(provider, model, messages, temperature, max_tokens)。
产物：统一输出结构 text/usage/raw_meta。
验收：切换 provider 不改业务代码，只改参数。
"""

import os
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI
from openai import (
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)
from dotenv import load_dotenv

load_dotenv()


# === 统一出参结构 ===
@dataclass
class LLMResponse:  # 统一 LLM 调用响应结构
    text: str
    usage: dict  # 用字典以兼容不同模型的消耗信息响应格式(标准是3个token字段)
    raw_meta: dict  # 原始 API 响应数据，包含后面定义的所有字段


# === 自定义异常层 ===
class LLMException(Exception):
    """密钥错误或无权限"""


class LLMAuthError(LLMException):
    """密钥错误或无权限"""


class LLMTimeoutError(LLMException):
    """超时错误"""


class LLMRateLimitError(LLMException):
    """请求频率超过限制"""


class LLMError(LLMException):
    """其他错误"""


# === provider -> client 工厂 ===
def _get_client(provider: str) -> OpenAI:
    """根据 provider 返回对应的 OpenAI 兼容客户端"""
    if provider == "openai":
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    elif provider == "deepseek":
        return OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
        )
    else:
        raise ValueError(f"不支持的 provider: {provider}")


# === 核心调用层 ===
def chat(
    provider: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> LLMResponse:
    """
    统一 LLM 调用入口。

    Args:
        provider:    "openai" 或 "deepseek"
        model:       模型名称字符串
        messages:    对话历史列表
        temperature: 输出随机性 (0.0 ~ 2.0)
        max_tokens:  最大输出 token 数

    Returns:
        LLMResponse: text / usage / raw_meta

    Raises:
        LLMAuthError, LLMTimeoutError, LLMRateLimitError, LLMError
    """
    client = _get_client(provider)
    start = time.time()

    # 调用 LLM 模型
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except AuthenticationError as e:
        raise LLMAuthError(f"[{provider}] 密钥错误：{e}") from e
    except RateLimitError as e:
        raise LLMRateLimitError(f"[{provider}] 触发限流，请稍后重试：{e}") from e
    except APITimeoutError as e:
        raise LLMTimeoutError(f"[{provider}] 请求超时：{e}") from e
    except APIConnectionError as e:
        raise LLMTimeoutError(f"[{provider}] 连接失败，检查网络或 BASE_URL：{e}") from e
    except APIStatusError as e:
        raise LLMError(
            f"[{provider}] API 返回错误状态 {e.status_code}：{e.message}"
        ) from e

    latency_ms = (time.time() - start) * 1000

    return LLMResponse(
        text=response.choices[0].message.content,
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        raw_meta={
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "finish_reason": response.choices[0].finish_reason,
        },
    )
