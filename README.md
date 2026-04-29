# 科研文献摘要

这是一个本地运行的每日科研文献摘要工作流，用于从专门的学术 Gmail 邮箱读取 Google Scholar alerts、期刊目录提醒、RSS 邮件订阅等邮件，提取论文条目，去重，调用 LLM 根据近期研究兴趣排序，并同时生成中文 Markdown 摘要和 HTML 浏览器阅读页。

## 一、第一次使用配置教程

### 1. 安装 Python 依赖

在项目目录运行：

```powershell
Set-Location E:\Researching\My-literature-digest
python -m pip install -e .[dev]
```

如果 PowerShell 对 `.[dev]` 解析有问题，可以改用：

```powershell
python -m pip install -e ".[dev]"
```

### 2. 创建本地配置文件

复制配置模板：

```powershell
Copy-Item config.example.yaml config.local.yaml
```

后续只修改 `config.local.yaml`。`config.example.yaml` 是参考模板，便于以后查看所有可用选项。

### 3. 准备 Gmail OAuth

1. 打开 Google Cloud Console。
2. 新建或选择一个项目。
3. 启用 Gmail API。
4. 创建 OAuth Client，应用类型选择 Desktop App。
5. 下载 OAuth 凭据 JSON 文件。
6. 把下载的文件重命名为 `credentials.json`，放到项目根目录：

```text
E:\Researching\My-literature-digest\credentials.json
```

第一次真实读取 Gmail 时，程序会打开浏览器让你登录并授权，随后自动生成 `token.json`。

不要把 `credentials.json`、`token.json`、`.env`、`config.local.yaml` 提交到 git。

### 4. 写近期研究兴趣

编辑 `research_interests.md`，直接用自然语言描述即可，例如：

```markdown
我近期在做五边形 COF 纳米管的热导率研究，方法上依赖机器学习势函数。
我希望优先关注纳米管热导率、声子输运、机器学习势函数、五边形框架材料、COF/MOF 纳米结构合成等方向。
暂时不太关注纯电催化、纯有机合成或和材料计算关系较弱的论文。
```

程序每次运行会先调用 LLM，把这段文字提炼为结构化研究兴趣画像，再用它给论文排序。

### 5. 先运行样例 dry-run

如果还没有配置 Gmail OAuth，可以先跑内置样例：

```powershell
python -m literature_digest --dry-run --sample
```

输出文件会写到：

```text
outputs\YYYY-MM-DD-digest.md
outputs\YYYY-MM-DD-digest.html
```

HTML 文件可以直接用浏览器打开，支持搜索、按高/中/低相关筛选、折叠查看来源信息、展示 TOC/邮件图片和跳转原文链接。

### 6. 运行真实 Gmail dry-run

准备好 `credentials.json` 后运行：

```powershell
python -m literature_digest --dry-run --max-emails 5
```

第一次会浏览器授权。建议先用 `--max-emails 5` 或 `--max-emails 10` 小批量检查解析效果。

### 7. 确认稳定后再考虑标记已读

默认不会删除邮件，也不会标记已读。确认输出稳定后，如果希望处理过的邮件自动从未读中移除，可在 `config.local.yaml` 中设置：

```yaml
gmail:
  mark_as_read: true
```

正式运行时仍建议先保留 `dry_run_default: true`，后续接入自动化后再按需要切换。

## 二、常用运行命令

运行测试：

```powershell
python -m pytest
```

样例 dry-run：

```powershell
python -m literature_digest --dry-run --sample
```

真实 Gmail dry-run，最多读取 5 封：

```powershell
python -m literature_digest --dry-run --max-emails 5
```

使用指定配置文件：

```powershell
python -m literature_digest --config config.local.yaml --dry-run --max-emails 10
```

## 三、配置文件说明

完整参数参考见 `config.example.yaml`。最常用的是这些：

```yaml
gmail:
  query: "is:unread"
  max_emails_per_run: 50
  mark_as_read: false

llm:
  provider: "codex_cli"
  model: "gpt-5.4-mini"
  reasoning_effort: "low"
  timeout_seconds: 120
  max_output_tokens: 4000

research_interests:
  path: "research_interests.md"

digest:
  output_dir: "outputs"
  output_formats:
    - "md"
    - "html"
  overwrite_existing: false
  include_low_relevance: true
  max_low_relevance: 80
```

Gmail query 可以用 Gmail 搜索语法，例如：

```yaml
gmail:
  query: "is:unread newer_than:7d"
```

如果你的学术邮箱很干净，可以保持默认 `is:unread`。如果未读邮件积累很多，第一次建议临时使用 `--max-emails 5` 控制处理量。

## 四、默认使用 Codex CLI

默认配置：

```yaml
llm:
  provider: "codex_cli"
  model: "gpt-5.4-mini"
  reasoning_effort: "low"
  timeout_seconds: 120
  max_output_tokens: 4000
  codex_cli:
    executable: "codex"
    extra_args: []
```

如果 `codex` 不在 PATH 中，把 `executable` 改为 `codex.exe` 的完整路径。

这个任务主要是提炼兴趣、分类和生成中文摘要，通常不需要高推理强度。建议从 `gpt-5.4-mini` + `low` 开始，摘要质量不够时再提高模型或推理强度。

## 五、DeepSeek 最省钱配置

截至 2026-04-28，DeepSeek 官方中文文档说明：

- OpenAI 兼容格式的 `base_url` 是 `https://api.deepseek.com`。
- 当前新模型名是 `deepseek-v4-flash` 和 `deepseek-v4-pro`。
- `deepseek-chat` 与 `deepseek-reasoner` 将于 2026-07-24 弃用。
- `deepseek-v4-flash` 的价格低于 `deepseek-v4-pro`，适合作为每日摘要的默认低成本模型。
- DeepSeek 支持 JSON Output；本项目会请求 JSON，便于稳定解析。
- DeepSeek 的上下文硬盘缓存默认开启，不需要额外改代码。

推荐的低成本配置：

```yaml
llm:
  provider: "openai_compatible"
  timeout_seconds: 120
  max_output_tokens: 3000
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

然后在 `.env` 中填写：

```text
DEEPSEEK_API_KEY=你的_deepseek_api_key
```

这个配置的思路是：

- 用 `deepseek-v4-flash`，优先降低单次摘要成本。
- 关闭思考模式，避免这类日常分类/摘要任务产生额外推理开销。
- `max_output_tokens` 设为 3000，控制异常长输出。
- 保持 JSON Output，提高结构化解析稳定性。

如果发现摘要质量不够，再切换为：

```yaml
model: "deepseek-v4-pro"
```

如果发现复杂相关性判断仍不稳定，再考虑开启思考模式：

```yaml
reasoning_effort: "high"
extra_body:
  thinking:
    type: "enabled"
```

但这通常会增加成本，不建议作为每日自动任务的默认设置。

## 六、安全约定

- 程序不删除邮件。
- `mark_as_read` 默认关闭。
- dry-run 不修改 Gmail 状态。
- `config.local.yaml`、`credentials.json`、`token.json`、`.env`、`data/`、`outputs/` 已加入 `.gitignore`。
- 不要在日志、README、配置模板中写真实 API key 或 OAuth token。

## 七、后续接入自动化

等手动 dry-run 稳定后，可以让 Codex Automations 每天、每周或每隔几天定时运行：

```powershell
Set-Location E:\Researching\My-literature-digest
python -m literature_digest --dry-run --max-emails 50
```

## DeepSeek API 配置说明

DeepSeek 的完整通俗说明见：[docs/deepseek-api-guide.md](docs/deepseek-api-guide.md)。

当前项目的 LLM 配置已拆分：

```yaml
llm:
  config_path: "config/llm/deepseek.local.yaml"
```

不同模型的详细参数放在独立文件中：

- `config/llm/codex_cli.example.yaml`
- `config/llm/deepseek.example.yaml`
- `config/llm/deepseek.local.yaml`

其中 `config/llm/*.local.yaml` 已加入 `.gitignore`。DeepSeek API key 不要写入 yaml，应写入 `.env`：

```env
DEEPSEEK_API_KEY=sk-你的真实key
```

如果之后希望处理后自动标记已读，把 `config.local.yaml` 中的 `gmail.mark_as_read` 改为 `true`，并使用非 dry-run 运行。

更详细的 Codex Automations、避免 Codex CLI 中间会话持久化、Windows 桌面一键运行方案见：

```text
docs\automation-and-shortcuts.md
```
