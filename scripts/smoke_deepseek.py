import time
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), #不同的api调用需要不同的api_key
    base_url=os.getenv("DEEPSEEK_BASE_URL"), #需要不同的base_url
)

def smoke_test():
    print("=== DeepSeek Smoke Test ===")
    start = time.time()

    try:
        response = client.chat.completions.create(
            model="deepseek-v3",  # 换DeepSeek模型
            messages=[
                {"role": "system", "content": "你是一个助手，请简洁回答。"},
                {"role": "user", "content": "用一句话介绍你自己。"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        elapsed = time.time() - start
        text = response.choices[0].message.content
        usage = response.usage

        print(f"✅ 响应成功")
        print(f"   内容：{text}")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   Token 用量：prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")

    except Exception as e:
        print(f"❌ 失败：{type(e).__name__}: {e}")
        print("排查方向：1) 检查 DEEPSEEK_API_KEY  2) 检查 DEEPSEEK_BASE_URL  3) 模型名是否为 deepseek-chat")

if __name__ == "__main__":
    smoke_test()