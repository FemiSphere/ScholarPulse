from literature_digest.interests import analyze_research_interests
from literature_digest.llm.base import extract_json_object
from literature_digest.llm.offline_stub import OfflineStubClient
from literature_digest.models import PaperEntry
from literature_digest.ranking import rank_papers


def test_ranking_uses_interest_profile_and_returns_chinese_fields():
    llm = OfflineStubClient()
    profile = analyze_research_interests("五边形 COF 纳米管热导率和机器学习势函数。", llm)
    papers = [
        PaperEntry(
            title="Machine-learning interatomic potentials for thermal transport in pentagonal COF nanotubes",
            abstract="Thermal conductivity and phonon transport.",
        ),
        PaperEntry(title="Organic synthesis of unrelated molecules"),
    ]

    ranked = rank_papers(papers, profile, llm)

    assert ranked[0].relevance == "high"
    assert ranked[0].title_zh.startswith("论文：")
    assert ranked[-1].relevance in {"medium", "low"}


class PartialRankingClient:
    def complete(self, prompt: str) -> str:
        return '{"papers":[{"index":0,"relevance":"high","score":0.8}]}'

    def complete_json(self, prompt: str):
        return extract_json_object(self.complete(prompt))


def test_ranking_falls_back_to_local_title_translation_when_title_missing():
    papers = [PaperEntry(title="Metal-modulated phonon transport in porphyrin-based MOFs")]

    ranked = rank_papers(
        papers,
        analyze_research_interests("COF 纳米管 热导率", OfflineStubClient()),
        PartialRankingClient(),
    )

    assert ranked[0].title_zh == "卟啉基 MOFs 中金属调控的声子输运"
