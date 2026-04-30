# 自动化运行与桌面一键运行

本文说明两种运行方式：

- 使用 Codex Automations 或系统计划任务定期运行。
- 在 Windows 桌面创建双击即可运行的快捷方式。

## 推荐命令

在项目根目录运行：

```powershell
python -m literature_digest --dry-run --max-emails 50
```

默认 `dry-run` 不会修改 Gmail 状态，也不会标记已读。确认稳定后，如果希望处理过的邮件自动标记为已读，需要同时满足：

- `config.local.yaml` 中 `gmail.mark_as_read: true`
- 运行时使用 `--no-dry-run`

正式运行示例：

```powershell
python -m literature_digest --no-dry-run --max-emails 50
```

项目不会删除邮件。

## Codex Automations 示例

每周一、周三、周五运行：

```text
每周一、周三、周五上午 9:00，在本地项目目录中运行：

python -m literature_digest --dry-run --max-emails 50

运行完成后只告诉我新生成的 md/html 文件路径和统计信息，不需要展开摘要内容。
```

每周运行一次：

```text
每周一上午 9:00，在本地项目目录中运行：

python -m literature_digest --dry-run --max-emails 100

运行完成后报告 outputs 目录中新生成的 digest 文件路径。
```

每隔几天运行一次：

```text
每 3 天上午 9:00，在本地项目目录中运行：

python -m literature_digest --dry-run --max-emails 80
```

## 避免 Codex CLI 中间会话长期保留

如果使用 Codex CLI 后端，可在模型配置中启用 ephemeral 模式：

```yaml
provider: "codex_cli"
timeout_seconds: 120
max_output_tokens: 3000

codex_cli:
  executable: "codex"
  model: "gpt-5.4-mini"
  reasoning_effort: "low"
  ephemeral: true
```

这会让程序调用：

```powershell
codex exec --ephemeral ...
```

如果仍然不希望摘要任务调用 Codex CLI，可改用 OpenAI-compatible 后端，例如 DeepSeek：

```yaml
llm:
  provider: "openai_compatible"
  config_path: "config/llm/deepseek.local.yaml"
```

## Windows 桌面一键运行

仓库提供：

```text
scripts\run_digest.ps1
scripts\run_digest.bat
```

双击 `scripts\run_digest.bat` 会：

- 自动定位项目根目录。
- 设置 Python UTF-8 环境变量。
- 运行 `python -m literature_digest`。
- 将日志保存到 `logs\digest-YYYYMMDD-HHMMSS.log`。

如果中文控制台显示异常，脚本中的固定提示会使用英文输出。

## 创建桌面快捷方式

在 PowerShell 中进入项目根目录后运行：

```powershell
$ProjectRoot = (Get-Location).Path
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ScholarPulse.lnk"
$Target = Join-Path $ProjectRoot "scripts\run_digest.bat"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Target
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$Shortcut.Save()
```

之后桌面会出现 `ScholarPulse` 快捷方式，双击即可运行。

## 邮件积累较多时的建议

处理速度主要取决于：

- Gmail 下载邮件正文和附件的速度。
- 邮件解析和去重速度。
- LLM 摘要与排序速度。

通常最慢的是 LLM。建议先小批量处理：

```powershell
python -m literature_digest --dry-run --max-emails 20
```

确认效果后再提高到：

```powershell
python -m literature_digest --dry-run --max-emails 50
```

如果一天内多次运行，程序会自动避免覆盖同名输出文件。
