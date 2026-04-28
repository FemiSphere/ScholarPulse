from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path

from .models import DigestRun, RankedPaper


def write_digest(run: DigestRun, output_dir: str | Path) -> Path:
    """Backward-compatible Markdown-only writer."""

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{run.date_label}-digest.md"
    target.write_text(render_markdown(run), encoding="utf-8")
    return target


def write_digests(run: DigestRun, output_dir: str | Path, formats: list[str] | None = None) -> list[Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    selected = [item.lower() for item in (formats or ["md", "html"])]
    written: list[Path] = []

    if "md" in selected or "markdown" in selected:
        markdown_path = target_dir / f"{run.date_label}-digest.md"
        markdown_path.write_text(render_markdown(run), encoding="utf-8")
        written.append(markdown_path)

    if "html" in selected:
        html_path = target_dir / f"{run.date_label}-digest.html"
        html_path.write_text(render_html(run, target_dir), encoding="utf-8")
        written.append(html_path)

    return written


def render_markdown(run: DigestRun) -> str:
    lines: list[str] = []
    lines.append(f"# 科研文献摘要 - {run.date_label}")
    lines.append("")
    if run.warnings:
        lines.append("## 运行提示")
        lines.extend(f"- {warning}" for warning in run.warnings)
        lines.append("")

    stats = run.stats
    lines.append("## 总体统计")
    lines.append(f"- 邮件读取数：{stats.emails_read}")
    lines.append(f"- 跳过无用邮件：{stats.skipped_emails}")
    lines.append(f"- 提取论文条目：{stats.paper_entries_extracted}")
    lines.append(f"- 去重移除：{stats.duplicates_removed}")
    lines.append(f"- 高相关论文：{stats.high_relevance}")
    lines.append(f"- 中相关论文：{stats.medium_relevance}")
    lines.append(f"- 低相关论文：{stats.low_relevance}")
    lines.append(f"- 样例模式：{'是' if stats.sample_mode else '否'}")
    lines.append("")

    lines.append("## 近期研究兴趣摘要")
    lines.append(run.interest_profile.summary_zh or "未生成研究兴趣摘要。")
    lines.append("")
    if run.interest_profile.high_priority_topics:
        lines.append("高优先级主题：" + "；".join(run.interest_profile.high_priority_topics))
        lines.append("")

    _append_markdown_section(lines, "高相关论文", [paper for paper in run.papers if paper.relevance == "high"])
    _append_markdown_section(lines, "中相关论文", [paper for paper in run.papers if paper.relevance == "medium"])
    _append_markdown_section(lines, "低相关论文", [paper for paper in run.papers if paper.relevance == "low"], short=True)

    if run.skipped:
        lines.append("## 跳过的邮件")
        for skipped in run.skipped:
            lines.append(f"- {skipped.subject} | {skipped.sender} | {skipped.reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_html(run: DigestRun, output_dir: str | Path | None = None) -> str:
    stats = run.stats
    stats_cards = [
        ("邮件读取", stats.emails_read),
        ("论文条目", stats.paper_entries_extracted),
        ("去重移除", stats.duplicates_removed),
        ("高相关", stats.high_relevance),
        ("中相关", stats.medium_relevance),
        ("低相关", stats.low_relevance),
        ("跳过邮件", stats.skipped_emails),
    ]
    warnings = "".join(f"<li>{escape(warning)}</li>" for warning in run.warnings)
    high_topics = run.interest_profile.high_priority_topics
    high_topic_html = "".join(f"<span>{escape(topic)}</span>" for topic in high_topics)
    paper_cards = "\n".join(_render_paper_card(paper, index, output_dir) for index, paper in enumerate(run.papers, 1))
    skipped_items = "".join(
        f"<li><strong>{escape(item.subject)}</strong><span>{escape(item.sender)}</span><em>{escape(item.reason)}</em></li>"
        for item in run.skipped
    )
    data = {
        "high": stats.high_relevance,
        "medium": stats.medium_relevance,
        "low": stats.low_relevance,
        "total": len(run.papers),
    }

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>科研文献摘要 - {escape(run.date_label)}</title>
  <style>
    :root {{
      --bg: #f6f4ee;
      --surface: #fffdf8;
      --surface-strong: #ffffff;
      --text: #202124;
      --muted: #646b73;
      --border: #ddd8cd;
      --accent: #0f766e;
      --accent-strong: #0b4f4a;
      --high: #a63822;
      --medium: #7a5b00;
      --low: #56616d;
      --shadow: 0 16px 36px rgba(32, 33, 36, 0.08);
      color-scheme: light;
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", system-ui, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
    }}
    a {{ color: var(--accent-strong); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    header {{
      padding: 34px 28px 24px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(180deg, #fffdf8 0%, #f6f4ee 100%);
    }}
    .shell {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; line-height: 1.2; font-weight: 760; letter-spacing: 0; }}
    .subtitle {{ margin: 0; color: var(--muted); font-size: 15px; }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(246, 244, 238, 0.94);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      padding: 14px 0;
    }}
    .toolbar-row {{ display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: center; }}
    input[type="search"] {{
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0 14px;
      background: var(--surface-strong);
      color: var(--text);
      font-size: 14px;
      outline: none;
    }}
    input[type="search"]:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12); }}
    .filters {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface-strong);
      color: var(--text);
      min-height: 40px;
      padding: 0 13px;
      font-size: 14px;
      cursor: pointer;
    }}
    button[aria-pressed="true"] {{ background: var(--accent); border-color: var(--accent); color: white; }}
    main {{ padding: 26px 0 56px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(7, minmax(110px, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }}
    .stat {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 13px 14px;
      min-height: 74px;
    }}
    .stat strong {{ display: block; font-size: 24px; line-height: 1.1; }}
    .stat span {{ color: var(--muted); font-size: 13px; }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 18px;
      box-shadow: var(--shadow);
    }}
    .panel h2, .section-title {{ margin: 0 0 12px; font-size: 20px; line-height: 1.3; }}
    .topics {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .topics span, .tag {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      background: #e6f2ef;
      color: var(--accent-strong);
      padding: 4px 10px;
      font-size: 12px;
    }}
    .paper-list {{ display: grid; gap: 16px; }}
    .paper-card {{
      background: var(--surface-strong);
      border: 1px solid var(--border);
      border-left: 5px solid var(--low);
      border-radius: 8px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .paper-card[data-level="high"] {{ border-left-color: var(--high); }}
    .paper-card[data-level="medium"] {{ border-left-color: var(--medium); }}
    .paper-card[data-level="low"] {{ border-left-color: var(--low); }}
    .paper-top {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .paper-card h3 {{ margin: 0 0 8px; font-size: 20px; line-height: 1.35; letter-spacing: 0; }}
    .meta {{ margin: 0 0 10px; color: var(--muted); font-size: 13px; }}
    .score {{
      flex: 0 0 auto;
      border-radius: 8px;
      border: 1px solid var(--border);
      padding: 7px 10px;
      color: var(--muted);
      font-size: 13px;
      background: #faf8f2;
    }}
    .summary {{ margin: 10px 0; }}
    details {{ margin-top: 10px; }}
    summary {{ cursor: pointer; color: var(--accent-strong); font-weight: 650; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
    .action {{
      display: inline-flex;
      align-items: center;
      min-height: 38px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #f7fbfa;
      text-decoration: none;
      font-size: 14px;
    }}
    .image-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 14px; }}
    .image-grid img {{
      width: 100%;
      max-height: 320px;
      object-fit: contain;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: white;
    }}
    .skipped-list {{ margin: 0; padding-left: 18px; }}
    .skipped-list span, .skipped-list em {{ color: var(--muted); margin-left: 8px; font-size: 13px; }}
    .empty {{ display: none; padding: 24px; text-align: center; color: var(--muted); }}
    footer {{ color: var(--muted); font-size: 12px; padding: 28px 0; }}
    @media (max-width: 860px) {{
      h1 {{ font-size: 27px; }}
      .toolbar-row {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .paper-top {{ display: block; }}
      .score {{ display: inline-flex; margin-bottom: 10px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="shell">
      <h1>科研文献摘要</h1>
      <p class="subtitle">{escape(run.date_label)} · 浏览器阅读版 · 共 {len(run.papers)} 篇候选论文</p>
    </div>
  </header>
  <nav class="toolbar" aria-label="阅读工具">
    <div class="shell toolbar-row">
      <input id="search" type="search" placeholder="搜索标题、摘要、主题、DOI 或来源邮件">
      <div class="filters" role="group" aria-label="相关性筛选">
        <button type="button" data-filter="all" aria-pressed="true">全部</button>
        <button type="button" data-filter="high" aria-pressed="false">高相关</button>
        <button type="button" data-filter="medium" aria-pressed="false">中相关</button>
        <button type="button" data-filter="low" aria-pressed="false">低相关</button>
      </div>
    </div>
  </nav>
  <main class="shell">
    <section class="stats" aria-label="总体统计">
      {''.join(f'<div class="stat"><strong>{value}</strong><span>{escape(label)}</span></div>' for label, value in stats_cards)}
    </section>
    {'<section class="panel"><h2>运行提示</h2><ul>' + warnings + '</ul></section>' if warnings else ''}
    <section class="panel">
      <h2>近期研究兴趣摘要</h2>
      <p>{escape(run.interest_profile.summary_zh or '未生成研究兴趣摘要。')}</p>
      {'<div class="topics">' + high_topic_html + '</div>' if high_topic_html else ''}
    </section>
    <h2 class="section-title">论文列表</h2>
    <section class="paper-list" id="papers" aria-live="polite">
      {paper_cards or '<p class="panel">暂无论文条目。</p>'}
    </section>
    <p class="empty" id="empty">当前筛选条件下没有匹配论文。</p>
    {'<section class="panel"><h2>跳过的邮件</h2><ul class="skipped-list">' + skipped_items + '</ul></section>' if skipped_items else ''}
    <footer>由本地 literature_digest 工作流生成。Markdown 与 HTML 文件包含相同 digest 内容，HTML 额外提供搜索、筛选和图片浏览。</footer>
  </main>
  <script type="application/json" id="digest-data">{escape(json.dumps(data, ensure_ascii=False))}</script>
  <script>
    const search = document.querySelector('#search');
    const buttons = Array.from(document.querySelectorAll('[data-filter]'));
    const cards = Array.from(document.querySelectorAll('.paper-card'));
    const empty = document.querySelector('#empty');
    let activeFilter = 'all';

    function applyFilters() {{
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {{
        const matchesLevel = activeFilter === 'all' || card.dataset.level === activeFilter;
        const matchesSearch = !query || card.dataset.search.includes(query);
        const show = matchesLevel && matchesSearch;
        card.hidden = !show;
        if (show) visible += 1;
      }}
      empty.style.display = visible ? 'none' : 'block';
    }}

    for (const button of buttons) {{
      button.addEventListener('click', () => {{
        activeFilter = button.dataset.filter;
        for (const item of buttons) item.setAttribute('aria-pressed', String(item === button));
        applyFilters();
      }});
    }}
    search.addEventListener('input', applyFilters);
  </script>
</body>
</html>
"""


def _append_markdown_section(lines: list[str], title: str, papers: list[RankedPaper], *, short: bool = False) -> None:
    lines.append(f"## {title}")
    if not papers:
        lines.append("暂无。")
        lines.append("")
        return

    for index, paper in enumerate(papers, start=1):
        entry = paper.entry
        link = f" | [链接]({entry.url})" if entry.url else ""
        doi = f" | DOI: `{entry.doi}`" if entry.doi else ""
        lines.append(f"### {index}. {paper.title_zh}")
        lines.append(f"- 原题：{entry.title}{link}{doi}")
        lines.append(f"- 相关性：{paper.relevance} / {paper.score:.2f}")
        if paper.matched_topics:
            lines.append(f"- 匹配主题：{'；'.join(paper.matched_topics)}")
        if short:
            lines.append(f"- 简注：{paper.reason_zh}")
        else:
            lines.append(f"- 中文摘要：{paper.summary_zh}")
            lines.append(f"- 推荐理由：{paper.reason_zh}")
        if entry.image_paths:
            lines.append("- TOC/邮件图片：")
            for image_path in entry.image_paths:
                lines.append(f"  - ![]({image_path})")
        lines.append(f"- 来源邮件：{entry.source_subject} | {entry.source_sender}")
        lines.append("")


def _render_paper_card(paper: RankedPaper, index: int, output_dir: str | Path | None) -> str:
    entry = paper.entry
    search_blob = " ".join(
        [
            entry.title,
            paper.title_zh,
            paper.summary_zh,
            paper.reason_zh,
            entry.doi,
            entry.source_subject,
            " ".join(paper.matched_topics),
        ]
    ).lower()
    topic_html = "".join(f'<span class="tag">{escape(topic)}</span>' for topic in paper.matched_topics)
    image_html = _render_images(entry.image_paths, output_dir)
    original_link = (
        f'<a class="action" href="{escape(entry.url)}" target="_blank" rel="noreferrer">打开原文</a>'
        if entry.url
        else ""
    )
    doi_html = f'<span>DOI: <code>{escape(entry.doi)}</code></span>' if entry.doi else ""
    return f"""
      <article class="paper-card" data-level="{escape(paper.relevance)}" data-search="{escape(search_blob)}">
        <div class="paper-top">
          <div>
            <h3>{index}. {escape(paper.title_zh)}</h3>
            <p class="meta">原题：{escape(entry.title)}</p>
          </div>
          <div class="score">{escape(_level_label(paper.relevance))} · {paper.score:.2f}</div>
        </div>
        {'<div class="topics">' + topic_html + '</div>' if topic_html else ''}
        <p class="summary">{escape(paper.summary_zh)}</p>
        <details>
          <summary>查看推荐理由与来源</summary>
          <p>{escape(paper.reason_zh)}</p>
          <p class="meta">来源邮件：{escape(entry.source_subject)} | {escape(entry.source_sender)}</p>
          {doi_html}
        </details>
        {image_html}
        <div class="actions">{original_link}</div>
      </article>
"""


def _render_images(paths: list[Path | str], output_dir: str | Path | None) -> str:
    if not paths:
        return ""
    items = []
    for path in paths:
        src = _image_src(path, output_dir)
        items.append(f'<img src="{escape(src)}" alt="TOC 或邮件图片" loading="lazy">')
    return '<div class="image-grid">' + "".join(items) + "</div>"


def _image_src(path: Path | str, output_dir: str | Path | None) -> str:
    raw = str(path)
    if raw.startswith(("http://", "https://", "data:", "file:")):
        return raw
    image_path = Path(raw)
    if image_path.is_absolute():
        return image_path.as_uri()
    if output_dir is not None:
        base = Path(output_dir).resolve()
        absolute = image_path.resolve()
        try:
            return os.path.relpath(absolute, base).replace("\\", "/")
        except ValueError:
            return absolute.as_uri()
    return image_path.as_posix()


def _level_label(level: str) -> str:
    return {"high": "高相关", "medium": "中相关", "low": "低相关"}.get(level, level)
