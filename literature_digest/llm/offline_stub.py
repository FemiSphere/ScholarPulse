from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .base import extract_json_object


@dataclass(slots=True)
class OfflineStubClient:
    """Deterministic fallback for tests and no-credential sample dry-runs only."""

    def complete(self, prompt: str) -> str:
        if "INTEREST_PROFILE_JSON" in prompt:
            return json.dumps(
                {
                    "current_projects": ["五边形 COF 纳米管热导率研究"],
                    "material_systems": ["五边形 COF", "框架材料", "纳米管"],
                    "methods": ["机器学习势函数", "计算材料科学"],
                    "properties": ["热导率", "声子", "热输运"],
                    "high_priority_topics": [
                        "五边形框架材料",
                        "机器学习势函数",
                        "纳米管热导率",
                        "热输运",
                    ],
                    "medium_priority_topics": ["AI for materials", "COF/MOF", "phonons"],
                    "deprioritized_topics": ["纯促销信息", "非学术营销"],
                    "summary_zh": "近期重点关注五边形 COF 纳米管、热导率与机器学习势函数交叉方向。",
                },
                ensure_ascii=False,
            )
        if "RANK_PAPERS_JSON" in prompt:
            papers = _extract_papers(prompt)
            ranked = []
            for item in papers:
                text = (item.get("title", "") + " " + item.get("abstract", "")).lower()
                score = 0.25
                if any(term in text for term in ["pentagonal", "penta", "cof", "nanotube"]):
                    score += 0.35
                if any(term in text for term in ["thermal", "phonon", "conductivity"]):
                    score += 0.25
                if any(term in text for term in ["machine learning", "interatomic potential", "nep"]):
                    score += 0.2
                relevance = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
                ranked.append(
                    {
                        "index": item["index"],
                        "relevance": relevance,
                        "score": round(min(score, 1.0), 2),
                        "title_zh": f"中文标题：{item.get('title', '')}",
                        "summary_zh": "基于邮件信息生成的离线样例摘要；真实运行时请使用 Codex CLI 或外置 API。",
                        "reason_zh": "与当前研究兴趣的匹配度由样例规则估计。",
                        "matched_topics": ["热导率", "机器学习势函数"] if relevance != "low" else [],
                    }
                )
            return json.dumps({"papers": ranked}, ensure_ascii=False)
        return "{}"

    def complete_json(self, prompt: str) -> dict[str, Any]:
        return extract_json_object(self.complete(prompt))


def _extract_papers(prompt: str) -> list[dict[str, Any]]:
    marker = "PAPERS_JSON:"
    start = prompt.find(marker)
    if start == -1:
        return []
    raw = prompt[start + len(marker) :].strip()
    match = re.search(r"(\[.*\])", raw, flags=re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []

