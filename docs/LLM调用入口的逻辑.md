# LLM 调用入口的逻辑

这篇文档解决的问题是：`app/llm_client.py` 为什么会写成现在这个样子，它到底在帮业务层解决什么麻烦。读完以后，你应该能不用背源码，也能自己复述这份封装的设计逻辑，并按同样思路写出一个简化版。

## 1. 这篇文档讲什么

先说结论：这不是一篇 OpenAI SDK 的全量教程，也不是在讲所有大模型能力，而是在拆解一个很具体的设计问题。

这个问题是：

- 业务层以后怎么用最少的心智负担去调用 LLM
- 不同 provider 的差异怎么收口
- 底层 SDK 的复杂细节怎么不要直接泄漏到业务层

所以，`app/llm_client.py` 的重点不是“功能多”，而是“入口稳”。

## 2. 先看这份代码的角色

先说结论：[`app/llm_client.py`](/C:/MyPython/job-copilot/app/llm_client.py) 是业务层和底层 SDK 之间的一层薄封装。

它不负责：

- 复杂业务流程
- Prompt 编排
- 多轮会话状态管理
- 模型能力对比

它主要负责 4 件事：

- 提供统一调用入口 `chat(...)`
- 根据 `provider` 创建对应客户端
- 把底层异常翻译成项目自己的异常
- 把原始响应整理成统一结构 `LLMResponse`

换句话说，这层代码不是在“做业务”，而是在“隔离变化”。

## 3. 用倒推法理解这份代码

倒推法的意思是：先看最终想达到什么效果，再倒着推需要哪些设计。

### 3.1 最终想要的效果是什么

业务层理想中的调用方式应该很简单：

```python
result = chat(provider="openai", model="gpt-4o-mini", messages=messages)
print(result.text)
```

业务代码最好不要关心这些问题：

- `OpenAI(...)` 客户端怎么初始化
- OpenAI 和 DeepSeek 的配置差在哪里
- 密钥和 `base_url` 从哪里来
- SDK 抛出来的异常叫什么
- 原始响应里该取哪几个字段

只要你认同“业务层应该尽量少管这些细节”，后面的设计就顺理成章了。

### 3.2 所以需要统一入口 `chat()`

先说结论：如果业务层想一行调用，就必须有一个统一入口把底层细节都包起来。

这就是为什么 [`app/llm_client.py`](/C:/MyPython/job-copilot/app/llm_client.py) 里最重要的函数是：

```python
chat(provider, model, messages, temperature, max_tokens)
```

这个函数本质上在做 4 件事：

1. 接收调用参数
2. 创建或获取客户端
3. 发起模型请求
4. 整理结果并处理异常

也就是说，`chat()` 是业务层唯一需要认识的主入口。

### 3.3 统一入口要稳定，所以要统一输出 `LLMResponse`

先说结论：如果入口统一了，但返回结果还是杂乱的，那封装只做了一半。

所以代码定义了 `LLMResponse`，把调用结果整理成三个部分：

- `text`：模型真正回答的内容
- `usage`：token 消耗信息
- `raw_meta`：一些补充元数据，比如 `provider`、`model`、耗时、`finish_reason`

这样做的好处是：

- 业务层只看自己需要的结构
- 上层代码不用每次都自己去拆 `response.choices[0]`
- 以后如果底层 SDK 响应结构变了，修改可以尽量收敛在封装层里

这里最重要的设计观念是：**统一输入很重要，统一输出更重要。**

### 3.4 多 provider 会带来初始化差异，所以拆 `_get_client()`

先说结论：`chat()` 应该负责“调用流程”，不应该塞满“不同 provider 的初始化分支”。

如果把这些逻辑都堆进 `chat()`，代码会越来越像这样：

- 如果是 `openai`，用哪组环境变量
- 如果是 `deepseek`，再用另一组环境变量
- 后面如果加新的 provider，又要继续扩展分支

为了不让核心调用流程被分支判断淹没，代码把“根据 provider 创建客户端”抽成了：

```python
_get_client(provider)
```

它的职责很单纯：

- 收到 `provider`
- 读取对应环境变量
- 返回一个可调用的 OpenAI 兼容客户端
- 如果 `provider` 不支持，就抛 `ValueError`

这一步的价值在于把两个问题拆开了：

- `chat()` 负责“怎么调”
- `_get_client()` 负责“调谁”

### 3.5 底层 SDK 异常不能直接外泄，所以做自定义异常层

先说结论：封装不只是为了少写几行代码，更重要的是不要让业务层直接依赖第三方库的错误语义。

底层 SDK 可能抛出：

- `AuthenticationError`
- `RateLimitError`
- `APITimeoutError`
- `APIConnectionError`
- `APIStatusError`

如果业务层直接去接这些异常，会有两个问题：

- 业务代码会和某个 SDK 强耦合
- 以后替换 SDK 或调整底层实现时，上层也要跟着改

所以代码在 [`app/llm_client.py`](/C:/MyPython/job-copilot/app/llm_client.py) 里定义了项目自己的异常：

- `LLMException`
- `LLMAuthError`
- `LLMTimeoutError`
- `LLMRateLimitError`
- `LLMError`

这一步的本质不是“重新起个名字”，而是建立项目自己的错误边界。

业务层以后只需要理解：

- 鉴权错了
- 超时或连接失败了
- 被限流了
- 其他错误

它不需要知道 SDK 内部到底用了哪一个异常类。

### 3.6 配置不能写死，所以用 `.env` + `os.getenv()`

先说结论：只要代码需要 API Key 或服务地址，就不应该把这些信息直接写死在源码里。

所以文件一开始会：

```python
load_dotenv()
```

然后在 `_get_client()` 里通过 `os.getenv()` 读取：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`

这么做的原因很实际：

- 密钥是敏感信息，不能硬编码
- 开发环境和部署环境的配置可能不同
- `base_url` 也可能因为 provider 不同而不同

这一步是在给前面的统一调用做配置层支持。

### 3.7 把整条倒推链路串起来

如果把这份代码的设计逻辑压缩成一条链，就是：

1. 业务层想一行调用
2. 所以需要统一入口 `chat()`
3. 统一入口想稳定，就要统一输出 `LLMResponse`
4. 多 provider 会带来初始化差异，所以拆 `_get_client()`
5. 底层 SDK 异常不能直接外泄，所以做自定义异常层
6. 配置不能写死，所以用 `.env` + `os.getenv()`

一句话概括：

**这份代码不是先想“怎么调 API”，而是先想“怎么让以后业务调起来更轻松”。**

## 4. 用顺推法生成对应路线图

如果你现在从零开始自己写类似代码，最自然的顺序不是直接追求“架构完整”，而是一步步把问题收口。

### 第一步：先跑通单 provider

目标：先证明模型能调通。

你最开始只需要做到：

- 导入 `OpenAI`、`os`、`time`、`load_dotenv`
- `load_dotenv()`
- 创建一个最简单的 `client = OpenAI(...)`
- 写一个最小版 `chat()`，把 `response.choices[0].message.content` 返回出去

验收标准：

- 能成功拿到模型回答
- 知道 `model` 和 `messages` 怎么传

这一阶段的核心不是“优雅”，而是“先通”。

### 第二步：把返回值统一起来

目标：不让调用方每次自己拆响应。

这时再做两件事：

- 定义 `LLMResponse`
- 在 `chat()` 里整理出 `text`、`usage`、`raw_meta`

验收标准：

- 外部调用不再直接接触原始 `response`
- 外部统一通过 `result.text`、`result.usage`、`result.raw_meta` 读结果

这一阶段开始从“能用”走向“好用”。

### 第三步：把 provider 差异抽出去

目标：让 `chat()` 聚焦调用，不负责到处判断分支。

这一步做的事情是：

- 新建 `_get_client(provider)`
- 把 `openai` 和 `deepseek` 的 `api_key`、`base_url` 分开
- 不支持的 provider 直接抛 `ValueError`

验收标准：

- 切换 provider 时，业务层只改参数
- `chat()` 主体逻辑基本不因为 provider 变化而变化

这一阶段是在降低耦合。

### 第四步：补异常翻译层

目标：让上层按业务语义处理错误，而不是按 SDK 细节处理错误。

这一步要做的是：

- 定义一组自定义异常
- 在 `try/except` 里把 SDK 异常映射成项目自己的异常

验收标准：

- 上层可以按“鉴权错误 / 限流 / 超时 / 其他错误”分类处理
- 业务层不用记忆 SDK 的异常名

这一阶段是在稳定接口边界。

### 第五步：补测试，证明封装真的有价值

目标：确认这不是“看起来整齐”，而是真的更易用。

可以直接对照 [`scripts/test_llm_client.py`](/C:/MyPython/job-copilot/scripts/test_llm_client.py) 来理解。

这个测试脚本做了三类验证：

- 用 `deepseek` 调一次
- 用 `openai` 调一次
- 传入非法 `provider`，看是否正确抛 `ValueError`

它还顺手验证了一个更重要的点：调用方拿到的是统一结果结构和统一异常语义。

验收标准：

- 成功场景能拿到 `text / usage / raw_meta`
- 错误场景能被分类捕获
- 切换 provider 时，上层代码几乎不需要改

## 5. 关键接口应该怎么理解

这一节不讲实现细节，只讲职责边界。

### `chat(...)`

它是主入口。

你可以把它理解为“对业务层暴露的统一门把手”。\
业务层最主要依赖的就是它，而不是底层 SDK。

### `LLMResponse`

它是统一出参结构。

你可以把它理解为“封装层和业务层之间约定好的返回格式”。\
只要这层约定稳定，外部调用就更容易保持稳定。

### `_get_client()`

它是 provider 到客户端的转换器。

你可以把它理解为“连接准备阶段”。\
它不负责真正的业务调用，只负责根据 provider 把客户端准备好。

### 自定义异常体系

它是错误边界。

你可以把它理解为“给业务层看的错误语言”。\
业务层不一定要理解 SDK 内部是怎么失败的，但它需要知道这次失败属于哪一类。

## 6. 调用链路图

用一条简单链路来看，整个调用过程是这样的：

```text
调用方
  -> chat(provider, model, messages, ...)
  -> _get_client(provider)
  -> OpenAI 兼容客户端
  -> client.chat.completions.create(...)
  -> 原始 response
  -> 整理成 LLMResponse
  -> 返回给调用方
```

如果你更喜欢图形化一点的表达，也可以这样看：

```mermaid
flowchart LR
    A["调用方"] --> B["chat(provider, model, messages, ...)"]
    B --> C["_get_client(provider)"]
    C --> D["OpenAI 兼容客户端"]
    D --> E["client.chat.completions.create(...)"]
    E --> F["原始 response"]
    F --> G["LLMResponse"]
    G --> H["返回给调用方"]
```

这个图想说明的重点只有一个：\
**调用方真正依赖的是** **`chat()`** **和** **`LLMResponse`，而不是底层 SDK 的全部细节。**

## 7. 对照测试理解这份封装的价值

如果你只看 [`app/llm_client.py`](/C:/MyPython/job-copilot/app/llm_client.py)，容易觉得它只是“包了一层”。\
但结合 [`scripts/test_llm_client.py`](/C:/MyPython/job-copilot/scripts/test_llm_client.py) 看，会更容易理解它的价值。

测试脚本的使用方式很简单：

- 调用 `chat(...)`
- 打印 `result.text`
- 打印 `result.usage`
- 打印 `result.raw_meta`
- 对不同错误做不同捕获

这里最关键的价值有两个：

- 测试脚本不需要自己创建不同 provider 的客户端
- 测试脚本可以按统一异常分类处理问题

也就是说，这份封装真正节省的不是几行代码，而是调用方需要重复思考的那些细节。

## 8. 常见误区

### 误区 1：统一入口等于功能很多

不是。\
统一入口的重点是入口一致，不是能力堆满。

`llm_client.py` 当前只解决一件核心事：把多 provider 的基础聊天调用收敛成一个稳定入口。

### 误区 2：封装只是为了少写几行代码

不是。\
真正的价值是：

- 隔离 provider 差异
- 隔离 SDK 差异
- 稳定业务层接口

少写几行只是顺带收益。

### 误区 3：既然有统一入口，就什么能力都该塞进来

不一定。\
如果把流式输出、函数调用、重试、日志、缓存、会话管理全塞进一个文件，它反而会失去“薄封装”的清晰性。

封装层应该优先解决当前明确存在的问题，而不是提前把未来所有可能都实现掉。

### 误区 4：异常翻译没有必要，直接抛原始异常就行

短期看似乎可以，长期通常会更乱。\
一旦业务层到处写 SDK 异常名，以后替换底层实现的成本就会迅速升高。

## 9. 自测清单

读完这篇文档后，你可以用下面这些问题检查自己是不是真的理解了：

- 你能不能一句话说清 `app/llm_client.py` 的职责
- 你能不能解释为什么业务层不应该直接操作 SDK 客户端
- 你能不能解释为什么 `chat()` 是主入口，而 `_get_client()` 不是
- 你能不能解释为什么 `LLMResponse` 比直接返回原始 `response` 更合适
- 你能不能解释为什么要把 SDK 异常转换成项目自己的异常
- 你能不能按“单 provider -> 统一出参 -> provider 工厂 -> 异常层 -> 测试”的顺序，把这份代码的生成路线讲出来

如果这些问题你都能比较顺畅地回答出来，说明你已经不是“看懂了代码表面”，而是真的抓住了它的设计逻辑。
