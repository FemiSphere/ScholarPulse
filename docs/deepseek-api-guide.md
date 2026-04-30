# DeepSeek API 使用说明：面向文献摘要工作流

本文说明如何把本项目的 LLM 后端从 Codex CLI 切换到 DeepSeek API，目标是让文献摘要任务更便宜、更快、更稳定。

本文依据 DeepSeek 中文 API 文档整理，查阅日期：2026-04-29。价格、模型名和政策可能变化，正式充值前请再看一次官方文档。

官方入口：

- DeepSeek API 文档：https://api-docs.deepseek.com/zh-cn/
- 首次调用 API：https://api-docs.deepseek.com/zh-cn/
- 模型与价格：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
- JSON Output：https://api-docs.deepseek.com/zh-cn/guides/json_mode
- 思考模式：https://api-docs.deepseek.com/zh-cn/guides/thinking_mode

## 1. 你需要理解的几个概念

### API

API 可以理解为“程序调用模型的接口”。本项目会把文献条目、研究兴趣和输出格式要求发送给 DeepSeek，DeepSeek 返回 JSON，程序再把 JSON 写成 Markdown 和 HTML。

你不需要手动写 HTTP 请求；本项目已经实现了 OpenAI-compatible API 调用。

### API Key

API Key 是 DeepSeek 识别账号和扣费的密钥，相当于密码。不要写进 git，不要放进公开文档。

本项目推荐把它写在项目根目录的 `.env` 文件中：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

`.env` 已加入 `.gitignore`。

### base_url

DeepSeek 支持 OpenAI-compatible 格式。OpenAI 格式的 `base_url` 是：

```text
https://api.deepseek.com
```

本项目会自动拼接 `/chat/completions`，最终调用的是对话补全接口。

### model

模型名决定你调用哪个模型。DeepSeek 当前文档列出的主要模型是：

- `deepseek-v4-flash`
- `deepseek-v4-pro`

文档也说明 `deepseek-chat` 和 `deepseek-reasoner` 将于 2026-07-24 弃用；新项目不建议再使用旧模型名。

本项目推荐使用：

```yaml
model: "deepseek-v4-flash"
```

原因是文献摘要任务主要是分类、翻译和结构化输出，不需要最高等级推理；`v4-flash` 更适合低成本、低延迟运行。

### token

Token 是模型计费和上下文长度的基本单位。可以粗略理解为字、词、数字或标点的切片。

DeepSeek 文档给出的粗略换算是：

- 1 个英文字符约 0.3 token
- 1 个中文字符约 0.6 token

实际用量以 API 返回的 `usage` 字段为准。

### 输入 token 和输出 token

本项目的一次 LLM 请求大致包括：

- 输入 token：研究兴趣、论文标题、期刊、链接、邮件片段、JSON 输出要求
- 输出 token：中文标题、相关性、摘要、推荐理由、匹配主题

积压邮件多时，不要只靠增大 `max_output_tokens`。更稳的方式是分批处理，并限制最终低相关条目数量。

### JSON Output

本项目依赖模型返回 JSON，因为程序要稳定解析字段，例如：

```json
{
  "papers": [
    {
      "index": 0,
      "relevance": "high",
      "score": 0.92,
      "title_zh": "中文题名",
      "summary_zh": "中文摘要",
      "reason_zh": "推荐理由",
      "matched_topics": ["热导率"]
    }
  ]
}
```

DeepSeek 文档要求：

- 请求中设置 `response_format: {"type": "json_object"}`
- prompt 中必须包含 `json` 字样，并给出 JSON 示例
- `max_tokens` 不能太小，否则 JSON 可能被截断
- JSON Output 仍可能偶发返回空 content，需要通过重试或 prompt 调整缓解

本项目已经做了这些事：

- `response_format_json: true`
- prompt 中包含 JSON schema
- 解析失败时会回退，不会删除邮件

### 思考模式

DeepSeek v4 支持思考模式，并且文档说明默认开启。思考模式适合复杂推理，但本项目的日常任务通常不需要。

为了更快、更省钱，本项目 DeepSeek 默认配置关闭思考模式：

```yaml
extra_body:
  thinking:
    type: "disabled"
```

关闭思考模式后，`temperature` 等普通采样参数才更有意义。文献摘要建议：

```yaml
temperature: 0.2
```

如果未来你想让模型做更复杂的跨论文综述，可以再尝试开启思考模式：

```yaml
reasoning_effort: "high"
extra_body:
  thinking:
    type: "enabled"
```

但这通常更慢，也可能更贵。

### 上下文硬盘缓存

DeepSeek 文档说明上下文硬盘缓存默认开启，不需要改代码。它会让重复前缀的输入更便宜。

对本项目来说，研究兴趣和 JSON 指令在多次请求中相似，因此可能受益于缓存。但缓存是尽力而为，不保证每次命中。

### 限速和排队

DeepSeek 会根据负载动态限制并发。达到限制时可能返回 HTTP 429。请求发出后，如果服务器排队，连接可能保持一段时间。

本项目建议：

```yaml
timeout_seconds: 300
```

如果积压邮件很多或 DeepSeek 服务繁忙，可以调到 600。

### 常见错误码

常见问题可以这样理解：

- 400：请求格式错误，多半是参数不兼容
- 401：API key 错误或没读取到
- 402：账户余额不足
- 422：参数错误，例如模型不支持某参数
- 429：请求过快或并发过高
- 500/503：服务端故障或繁忙，稍后重试

## 2. 本项目的配置结构

主配置文件只选择一个 LLM 配置文件：

```yaml
llm:
  config_path: "config/llm/deepseek.local.yaml"
```

具体模型参数放在独立文件里：

```text
config/llm/codex_cli.example.yaml
config/llm/deepseek.example.yaml
config/llm/deepseek.local.yaml
```

其中：

- `*.example.yaml` 是模板，可以提交 git
- `*.local.yaml` 是本地真实配置，已被 `.gitignore` 忽略

## 3. 第一次启用 DeepSeek

### 第一步：创建 API key

打开 DeepSeek 平台创建 API key：

```text
https://platform.deepseek.com/
```

创建后只复制一次，后续平台通常不会再次完整显示。

### 第二步：写入 .env

在项目根目录创建或编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

不要把 key 写到 README、yaml 模板、聊天记录或 git commit 里。

### 第三步：准备 DeepSeek 本地配置

本项目已经提供模板：

```text
config/llm/deepseek.example.yaml
```

复制为：

```text
config/llm/deepseek.local.yaml
```

推荐内容：

```yaml
provider: "openai_compatible"
timeout_seconds: 300
max_output_tokens: 4000

openai_compatible:
  base_url: "https://api.deepseek.com"
  api_key_env: "DEEPSEEK_API_KEY"
  model: "deepseek-v4-flash"
  temperature: 0.2
  reasoning_effort: ""
  response_format_json: true
  extra_body:
    thinking:
      type: "disabled"
```

### 第四步：主配置指向 DeepSeek

在 `config.local.yaml` 中设置：

```yaml
llm:
  config_path: "config/llm/deepseek.local.yaml"
```

### 第五步：先跑 sample

```powershell
python -m literature_digest --dry-run --sample
```

如果 sample 成功，再跑真实 Gmail：

```powershell
python -m literature_digest --dry-run --max-emails 5
```

## 4. 推荐参数怎么选

### 日常低成本配置

适合每周或每几天处理一次：

```yaml
model: "deepseek-v4-flash"
temperature: 0.2
max_output_tokens: 4000
extra_body:
  thinking:
    type: "disabled"
```

### 邮件积压很多时

建议分批，而不是一次塞入 200 封：

```powershell
python -m literature_digest --max-emails 50
```

如果你打开了：

```yaml
gmail:
  mark_as_read: true
```

每次成功处理后会把这批邮件标记为已读，下一次运行会继续处理剩余未读邮件。

如果仍在 dry-run，邮件不会标记已读，每次会重复处理同一批。

### 输出太长时

优先调这些：

```yaml
digest:
  max_high_relevance: 20
  max_medium_relevance: 30
  max_low_relevance: 80
```

不建议把 `max_output_tokens` 设置得很大来解决最终文件变长的问题。`max_output_tokens` 是单次模型返回上限；最终 Markdown/HTML 文件是本地生成的。

## 5. 安全注意事项

- API key 只放 `.env`
- `config/llm/*.local.yaml` 不提交 git
- 不在日志中打印 API key
- 不把 `token.json`、`credentials.json`、`.env` 发给别人
- 先 dry-run，再考虑 `mark_as_read: true`

## 6. 当前项目里的文件分工

- `config.example.yaml`：主配置模板，只选择一个 LLM 配置文件
- `config.local.yaml`：你的本地主配置，已忽略
- `config/llm/codex_cli.example.yaml`：Codex CLI 模板
- `config/llm/deepseek.example.yaml`：DeepSeek 模板
- `config/llm/deepseek.local.yaml`：你的 DeepSeek 本地配置，已忽略
- `.env`：保存 `DEEPSEEK_API_KEY`
