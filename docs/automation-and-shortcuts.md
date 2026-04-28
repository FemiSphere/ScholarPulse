# 自动化运行与桌面一键运行说明

本文说明两种运行方式：

- 使用 Codex Automations 每周或每隔几天自动运行。
- 在 Windows 桌面创建一个双击即可运行的快捷方式。

## 1. 推荐运行命令

项目根目录：

```powershell
E:\Researching\My-literature-digest
```

推荐命令：

```powershell
Set-Location E:\Researching\My-literature-digest
python -m literature_digest --dry-run --max-emails 50
```

默认 `dry-run` 不会修改 Gmail 状态，也不会标记已读。确认稳定后，如果你想让处理过的邮件自动标记为已读，需要同时满足：

- `config.local.yaml` 中 `gmail.mark_as_read: true`
- 运行时使用 `--no-dry-run`

正式运行命令示例：

```powershell
Set-Location E:\Researching\My-literature-digest
python -m literature_digest --no-dry-run --max-emails 50
```

## 2. Codex Automations 设置建议

在 Codex Automations 中创建定时任务时，任务内容建议写成：

```text
每周一、周三、周五上午 9:00，在本地项目 E:\Researching\My-literature-digest 中运行：

python -m literature_digest --dry-run --max-emails 50

运行完成后只告诉我输出的 md/html 文件路径和统计信息，不需要展开摘要内容。
```

如果你只想每周运行一次，可以写成：

```text
每周一上午 9:00，在本地项目 E:\Researching\My-literature-digest 中运行：

python -m literature_digest --dry-run --max-emails 100

运行完成后报告 outputs 目录中新生成的 digest 文件路径。
```

如果你想每隔几天运行一次，可以写成：

```text
每 3 天上午 9:00，在本地项目 E:\Researching\My-literature-digest 中运行：

python -m literature_digest --dry-run --max-emails 80
```

## 3. 避免 Codex CLI 中间会话出现在项目列表中

本项目默认通过 Codex CLI 做研究兴趣提炼和论文排序。为了避免每次摘要调用产生持久化的 Codex 中间会话，配置模板中已经加入：

```yaml
llm:
  provider: "codex_cli"
  codex_cli:
    executable: "codex"
    ephemeral: true
```

这会让程序调用：

```powershell
codex exec --ephemeral ...
```

`--ephemeral` 的作用是让 Codex CLI 以非持久化方式运行，不把这些摘要过程保存成长期会话文件，从而减少它们出现在 Codex 项目/会话列表中的可能性。

如果你仍然看到相关中间会话，建议改用外置便宜模型执行每日任务，例如 DeepSeek：

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
    response_format_json: true
    extra_body:
      thinking:
        type: "disabled"
```

这样摘要任务就不会再调用 Codex CLI。

## 4. Windows 桌面一键运行

仓库里已经提供两个脚本：

```text
scripts\run_digest.ps1
scripts\run_digest.bat
```

双击 `scripts\run_digest.bat` 会执行：

```powershell
python -m literature_digest --dry-run --max-emails 50
```

并把日志保存到：

```text
logs\digest-YYYYMMDD-HHMMSS.log
```

### 创建桌面快捷方式

在 PowerShell 中运行：

```powershell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "科研文献摘要.lnk"
$Target = "E:\Researching\My-literature-digest\scripts\run_digest.bat"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = "E:\Researching\My-literature-digest"
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$Shortcut.Save()
```

之后桌面会出现“科研文献摘要”快捷方式。双击即可运行。

## 5. 邮件积累较多时的速度

处理速度主要取决于三件事：

- Gmail 下载邮件正文和图片附件的速度。
- 邮件解析和去重速度。
- LLM 摘要和排序速度。

其中最慢的通常是 LLM。当前实现会按批次排序论文，默认每批 20 篇。命令行会显示：

- 当前阶段
- 邮件过滤进度
- 解析和去重数量
- LLM 排序批次进度
- 总耗时

如果邮件积累较多，建议先限制数量：

```powershell
python -m literature_digest --dry-run --max-emails 20
```

确认效果后再提高到：

```powershell
python -m literature_digest --dry-run --max-emails 50
```

如果不想显示进度，可加：

```powershell
python -m literature_digest --dry-run --max-emails 50 --quiet
```
