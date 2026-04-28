from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .llm import LLMClient
from .models import InterestProfile


def read_research_interests(path: str | Path) -> str:
    interests_path = Path(path)
    if not interests_path.exists():
        raise FileNotFoundError(f"Research interests file not found: {interests_path}")
    return interests_path.read_text(encoding="utf-8").strip()


def analyze_research_interests(text: str, llm: LLMClient) -> InterestProfile:
    prompt = f"""
INTEREST_PROFILE_JSON

你将读取一段研究兴趣说明。请只输出一个 JSON 对象，不要输出 Markdown。
字段必须包含：
- current_projects: string[]
- material_systems: string[]
- methods: string[]
- properties: string[]
- high_priority_topics: string[]
- medium_priority_topics: string[]
- deprioritized_topics: string[]
- summary_zh: string

要求：
1. 只根据用户文本提炼，不要使用固定模板关键词替代用户意图。
2. high_priority_topics 应体现近期最该优先推荐的交叉主题。
3. deprioritized_topics 可为空数组。

研究兴趣文本：
{text}
""".strip()
    payload = llm.complete_json(prompt)
    return profile_from_payload(payload)


def fallback_interest_profile(text: str) -> InterestProfile:
    """Create a lightweight profile without calling an LLM for empty digest runs."""

    summary = re.sub(r"\s+", " ", text).strip()
    if len(summary) > 220:
        summary = summary[:220].rstrip() + "..."
    topics = _extract_topic_phrases(text)
    payload = {
        "current_projects": [summary] if summary else [],
        "material_systems": [],
        "methods": [],
        "properties": [],
        "high_priority_topics": topics,
        "medium_priority_topics": [],
        "deprioritized_topics": [],
        "summary_zh": summary or "未填写近期研究兴趣。",
    }
    return profile_from_payload(payload)


def profile_from_payload(payload: dict[str, Any]) -> InterestProfile:
    return InterestProfile(
        current_projects=_string_list(payload.get("current_projects")),
        material_systems=_string_list(payload.get("material_systems")),
        methods=_string_list(payload.get("methods")),
        properties=_string_list(payload.get("properties")),
        high_priority_topics=_string_list(payload.get("high_priority_topics")),
        medium_priority_topics=_string_list(payload.get("medium_priority_topics")),
        deprioritized_topics=_string_list(payload.get("deprioritized_topics")),
        summary_zh=str(payload.get("summary_zh", "")).strip(),
        raw=payload,
    )


def profile_to_json(profile: InterestProfile) -> str:
    return json.dumps(profile.raw or {
        "current_projects": profile.current_projects,
        "material_systems": profile.material_systems,
        "methods": profile.methods,
        "properties": profile.properties,
        "high_priority_topics": profile.high_priority_topics,
        "medium_priority_topics": profile.medium_priority_topics,
        "deprioritized_topics": profile.deprioritized_topics,
        "summary_zh": profile.summary_zh,
    }, ensure_ascii=False, indent=2)


def _extract_topic_phrases(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text)
    parts = re.split(r"[，,。；;\n]", normalized)
    topics = [part.strip(" ：:") for part in parts if 4 <= len(part.strip()) <= 40]
    return topics[:8]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []

