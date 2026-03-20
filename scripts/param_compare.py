# scripts/param_compare.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.llm_client import chat

# === 固定3个测试问题 ===
QUESTIONS = [
    "解释什么是机器学习",
    "解释什么是RAG",
    "解释什么是top_p",
]

# === 测试矩阵： provider / model / temperature ===
CONFIG = [
    # deepseek
    {"provider": "deepseek", "model": "deepseek-v3", "temperature": 0.0},
    {"provider": "deepseek", "model": "deepseek-v3", "temperature": 0.7},
    {"provider": "deepseek", "model": "deepseek-v3", "temperature": 1.5},
    # openai
    {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.0},
    {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.7},
    {"provider": "openai", "model": "gpt-4o-mini", "temperature": 1.5},
]

SYSTEM_PROMPT = "你是一个简洁的助手，回答不超过两句话。"

results = []

# === 测试循环 ===
for question in QUESTIONS:
    print(f"\n{'='*50}")
    print(f"测试问题：{question}")
    print(f"{'='*50}")

    for config in CONFIG:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        try:
            res = chat(
                provider=config["provider"],
                model=config["model"],
                messages=messages,
                temperature=config["temperature"],
                max_tokens=200,
            )
            label = f"{config['model']} | temp={config['temperature']}"
            print(f"\n[{label}]")
            print(f"  回答   : {res.text.strip()}")
            print(
                f"  tokens : {res.usage['total_tokens']} | 耗时: {res.raw_meta['latency_ms']}ms"
            )

            results.append(
                {
                    "question": question,
                    "label": label,
                    "text": res.text.strip(),
                    "total_tokens": res.usage["total_tokens"],
                    "latency_ms": res.raw_meta["latency_ms"],
                }
            )
        except Exception as e:
            print(f"  ❌ 失败: {e}")


print("\n\n✅ 全部测试完成，请根据输出填写 evaluation/week1_model_compare.md")
