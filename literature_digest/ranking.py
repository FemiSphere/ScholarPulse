from __future__ import annotations

import json
from typing import Any

from .interests import profile_to_json
from .llm import LLMClient
from .models import InterestProfile, PaperEntry, RankedPaper, RelevanceLevel


def rank_papers(
    entries: list[PaperEntry],
    profile: InterestProfile,
    llm: LLMClient,
    *,
    batch_size: int = 20,
) -> list[RankedPaper]:
    ranked: list[RankedPaper] = []
    for offset in range(0, len(entries), batch_size):
        batch = entries[offset : offset + batch_size]
        payload = _rank_batch(batch, profile, llm, offset)
        ranked.extend(payload)
    return sorted(ranked, key=lambda item: item.score, reverse=True)


def _rank_batch(
    entries: list[PaperEntry],
    profile: InterestProfile,
    llm: LLMClient,
    offset: int,
) -> list[RankedPaper]:
    papers_json = [
        {
            "index": offset + index,
            "title": entry.title,
            "doi": entry.doi,
            "url": entry.url,
            "authors": entry.authors,
            "venue": entry.venue,
            "abstract": entry.abstract[:1600],
            "source_subject": entry.source_subject,
        }
        for index, entry in enumerate(entries)
    ]
    prompt = f"""
RANK_PAPERS_JSON

你是计算材料与 AI for materials 方向的中文科研助理。请根据“近期研究兴趣画像”判断每篇论文和当前课题的相关性，并生成中文摘要。
只输出一个 JSON 对象，不要输出 Markdown。

输出格式：
{{
  "papers": [
    {{
      "index": 0,
      "relevance": "high|medium|low",
      "score": 0.0,
      "title_zh": "...",
      "summary_zh": "...",
      "reason_zh": "...",
      "matched_topics": ["..."]
    }}
  ]
}}

评分要求：
- high: 与当前研究兴趣画像中的近期课题、材料体系、方法、物性存在强交叉。
- medium: 与其中一到两个维度相关，但不是近期主线。
- low: 学术上可能有用，但与当前兴趣关系较弱。
- score 为 0 到 1。
- 只根据兴趣画像和论文信息判断，不要引入未在画像中出现的固定偏好。

近期研究兴趣画像：
{profile_to_json(profile)}

PAPERS_JSON:
{json.dumps(papers_json, ensure_ascii=False)}
""".strip()
    payload = llm.complete_json(prompt)
    by_index = _payload_by_index(payload)
    result: list[RankedPaper] = []
    for local_index, entry in enumerate(entries):
        absolute_index = offset + local_index
        item = by_index.get(absolute_index, {})
        result.append(_ranked_from_payload(entry, item))
    return result


def _payload_by_index(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for item in payload.get("papers", []):
        if not isinstance(item, dict):
            continue
        try:
            result[int(item["index"])] = item
        except (KeyError, TypeError, ValueError):
            continue
    return result


def _ranked_from_payload(entry: PaperEntry, payload: dict[str, Any]) -> RankedPaper:
    relevance = str(payload.get("relevance", "low")).lower()
    if relevance not in {"high", "medium", "low"}:
        relevance = "low"
    try:
        score = float(payload.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    return RankedPaper(
        entry=entry,
        relevance=relevance,  # type: ignore[arg-type]
        score=max(0.0, min(score, 1.0)),
        title_zh=str(payload.get("title_zh") or entry.title),
        summary_zh=str(payload.get("summary_zh") or "LLM 未返回摘要。"),
        reason_zh=str(payload.get("reason_zh") or "LLM 未返回相关性理由。"),
        matched_topics=[str(item) for item in payload.get("matched_topics", []) if str(item).strip()],
    )


def count_relevance(papers: list[RankedPaper], level: RelevanceLevel) -> int:
    return sum(1 for paper in papers if paper.relevance == level)

