# scripts/test_llm_client.py
# 测试 llm_client 模块的统一调用入口和异常处理

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.llm_client import (
    chat,
    LLMAuthError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMError,
)

MESSAGES = [
    {"role": "system", "content": "你是一个简洁的助手，回答不超过两句话。"},
    {"role": "user", "content": "什么是 API？"},
]


def test_provider(provider: str, model: str):
    """测试指定 provider 和 model 的调用"""
    print(f"\n{'='*50}")
    print(f"测试 provider={provider}  model={model}")
    print(f"{'='*50}")
    try:
        result = chat(provider=provider, model=model, messages=MESSAGES)
        print(f"✅ text     : {result.text}")
        print(f"   usage    : {result.usage}")
        print(f"   raw_meta : {result.raw_meta}")
    except LLMAuthError as e:
        print(f"❌ 鉴权错误: {e}")
    except LLMRateLimitError as e:
        print(f"❌ 限流: {e}")
    except LLMTimeoutError as e:
        print(f"❌ 超时/网络: {e}")
    except LLMError as e:
        print(f"❌ 未知错误: {e}")


if __name__ == "__main__":
    test_provider("deepseek", "deepseek-v3")
    test_provider("openai", "gpt-4o-mini")

    print(f"\n{'='*50}")
    print("测试非法 provider（预期报 ValueError）")
    try:
        chat(provider="nonexistent", model="xxx", messages=MESSAGES)
    except ValueError as e:
        print(f"✅ 正确捕获 ValueError: {e}")
