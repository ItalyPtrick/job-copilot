"""
OpenAI API 冒烟测试脚本

冒烟测试（Smoke Test）：一种快速验证系统基本功能是否正常的测试方法。
就像电子设备首次通电时检查是否冒烟一样，验证最核心的功能能否工作。
"""

# ==================== 导入依赖库 ====================

import time
from openai import OpenAI
from dotenv import load_dotenv
import os

# ==================== 环境配置 ====================

load_dotenv()

# ==================== 创建 OpenAI 客户端 ====================

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# ==================== 冒烟测试函数 ====================

def smoke_test():
    print("=== OpenAI Smoke Test ===")
    start = time.time()  # 记录开始时间

    try:
        response = client.chat.completions.create(
            model="glm-4.5-flash",  # 指定模型测试
            messages=[
                {"role": "system", "content": "你是一个助手，请简洁回答。"},  # 系统提示
                {"role": "user", "content": "用一句话介绍你自己。"},  # 用户提示
            ],
            temperature=0.7,  # 温度参数，控制响应的随机性
            top_p=0.9,  # 样本参数，控制响应的随机性
            frequency_penalty=0.0,  # 频率惩罚参数，控制重复性
            presence_penalty=0.0,  # 存在惩罚参数，控制重复性
            max_tokens=100,  # 最大生成 token 数量，控制响应长度
        )

        elapsed = time.time() - start  # 计算耗时
        text = response.choices[0].message.content  # 提取模型响应内容
        usage = response.usage  # 提取模型调用统计信息

        print(f"✅ 响应成功")
        print(f"   内容：{text}")
        print(f"   耗时：{elapsed:.2f}s")
        print(f"   Token 用量：prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}") # 打印 token 用量: 提示词 token 数量, 生成 token 数量, 总 token 数量

    except Exception as e:
        print(f"❌ 失败：{type(e).__name__}: {e}")  # 打印异常信息
        print("排查方向：1) 检查 OPENAI_API_KEY  2) 检查 OPENAI_BASE_URL  3) 检查网络")  # 打印排查方向

# ==================== 程序入口 ====================

if __name__ == "__main__":
    smoke_test()
