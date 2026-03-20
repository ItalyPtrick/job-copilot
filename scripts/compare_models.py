import time
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

PROMPT = "请用 3 个要点总结：Python 异步编程的核心概念是什么？" # 比较不同模型的性能和响应时间

MODELS = [
    {
        "label": "OpenAI gpt-4o-mini", # 第一个模型：gpt-4o-mini
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "model": "gpt-4o-mini",
    },
    {
        "label": "DeepSeek deepseek-v3", # 第二个模型：deepseek-v3
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL"),
        "model": "deepseek-v3",
    },
]

for cfg in MODELS: # 遍历每个模型配置
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    print(f"\n{'='*50}")
    print(f"模型：{cfg['label']}")
    print(f"{'='*50}")

    start = time.time()
    try:
        response = client.chat.completions.create( # 调用模型生成响应
            model=cfg["model"], # 模型名称
            messages=[{"role": "user", "content": PROMPT}], # 输入提示
            temperature=0.7, # 温度参数，控制生成文本的随机性
            # 0.0 表示完全确定性，0.5 表示中等随机性，1.0 表示完全随机性
            # 建议使用 0.7 或 0.9 等值
            max_tokens=300,
        )
        elapsed = time.time() - start # 计算响应时间
        print(response.choices[0].message.content) # 打印模型响应
        print(f"\n耗时: {elapsed:.2f}s | Tokens: {response.usage.total_tokens}") # 打印响应时间和Token用量
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}") # 打印异常信息