# Week 1 复盘

## 完成情况

| 验收项 | 状态 | 备注 |
|--------|------|------|
| OpenAI / DeepSeek 双通道可切换 | ✅ |
| CLI 多轮可用且支持清空 | ✅ |
| POST /chat 稳定可用 | ✅ |
| README 可帮助他人独立跑通 | ✅ |
| 第 2 周可直接复用本周代码结构 | ✅ |

## 本周学到的最重要的 3 件事

1. 每次发送给LLM模型的消息，应该包含过去的所有对话记录
2. 自定义返回的JSON格式，包含text、usage、raw_meta等字段
3. HTTP 无状态 → 服务端用 session_id 作为 key 在内存里维护每个用户的 history → 每次请求根据 session_id 取出 history 拼进 messages 发给模型。

## 本周遇到的最大障碍

1.理解temperature参数的作用。<- 多自己尝试
2.如何限制发送给LLM模型的history长度。<- if len(history) > max_messages:history = history[-max_messages:]

## 现在还没想清楚的问题

什么是RAG？还需要创建什么路由？

## 第 2 周直接可复用的东西

- app/llm_client.py：统一调用层，直接复用
- app/main.py：FastAPI 底座，下周在此基础上叠加功能
- .env 配置结构：下周新增字段直接往里加