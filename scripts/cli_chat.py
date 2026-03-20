# scripts/cli_chat.py

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.llm_client import (
    chat,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMError,
)

# === 配置 ===
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "你是一个简洁、友好的助手。"
MAX_HISTORY_ROUNDS = 10

# === /help信息 ===
HELP_TEXT = """
可用命令：
  /clear    清空对话历史，重新开始
  /history  查看当前对话历史条数
  /exit     退出程序
  /help     显示此帮助
"""


def trim_history(history: list[dict]) -> list[dict]:
    """
    保留最近 MAX_HISTORY_ROUNDS 轮。
    每轮 = user + assistant 两条，所以最多保留 MAX_HISTORY_ROUNDS * 2 条。
    """
    max_messages = MAX_HISTORY_ROUNDS * 2
    if len(history) > max_messages:
        history = history[-max_messages:]  # 从倒数第 max_messages 个元素开始，取到最后
    return history


def main():
    print(f"=== CLI 多轮对话 ===")
    print(f"模型：{DEFAULT_PROVIDER} / {DEFAULT_MODEL}")
    print(f"输入 /help 查看命令，/exit 退出\n")

    history: list[dict] = []

    while True:
        try:
            user_input = input("你：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已退出。")
            break

        # 空输入跳过
        if not user_input:
            continue

        # ── 命令处理 ──────────────────────────────────────
        if user_input == "/exit":
            print("再见！")
            break

        elif user_input == "/clear":
            history = []
            print("✅ 对话历史已清空。\n")
            continue

        elif user_input == "/history":
            rounds = len(history) // 2
            print(
                f"当前对话：{rounds} 轮 / 最大 {MAX_HISTORY_ROUNDS} 轮（{len(history)} 条消息）\n"
            )
            continue

        elif user_input == "/help":
            print(HELP_TEXT)
            continue

        elif user_input.startswith("/"):
            print(f"未知命令：{user_input}，输入 /help 查看可用命令。\n")
            continue

        # ── 正常对话 ──────────────────────────────────────
        history.append(
            {"role": "user", "content": user_input}
        )  # 将用户消息添加到对话历史
        history = trim_history(history)  # 裁剪历史，保留最近 N 轮对话

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + history  # 系统提示 + 对话历史

        try:
            result = chat(
                provider=DEFAULT_PROVIDER,
                model=DEFAULT_MODEL,
                messages=messages,
            )
            reply = result.text
            history.append({"role": "assistant", "content": reply})

            print(f"\nAI：{reply}")
            print(
                f"    [tokens: {result.usage['total_tokens']} | 耗时: {result.raw_meta['latency_ms']}ms]\n"
            )

        except LLMAuthError as e:
            print(f"❌ 鉴权错误：{e}\n")
        except LLMRateLimitError as e:
            print(f"❌ 限流，请稍后重试：{e}\n")
        except LLMTimeoutError as e:
            print(f"❌ 超时/网络问题：{e}\n")
        except LLMError as e:
            print(f"❌ 未知错误：{e}\n")


if __name__ == "__main__":
    main()
