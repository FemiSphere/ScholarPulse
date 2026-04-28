from pathlib import Path

from literature_digest.digest import write_digests
from literature_digest.models import DigestRun, InterestProfile, PaperEntry, RankedPaper, RunStats


def test_write_digests_creates_markdown_and_html(tmp_path):
    image_path = tmp_path / "toc.png"
    image_path.write_bytes(b"fake image bytes")
    run = DigestRun(
        date_label="2026-04-28",
        stats=RunStats(
            emails_read=1,
            paper_entries_extracted=1,
            high_relevance=1,
        ),
        interest_profile=InterestProfile(
            summary_zh="关注五边形 COF 纳米管热导率。",
            high_priority_topics=["五边形 COF", "热导率"],
        ),
        papers=[
            RankedPaper(
                entry=PaperEntry(
                    title="Thermal conductivity in pentagonal COF nanotubes",
                    url="https://example.org/paper",
                    doi="10.1234/example",
                    source_subject="Journal TOC",
                    source_sender="alerts@example.org",
                    image_paths=[image_path],
                ),
                relevance="high",
                score=0.95,
                title_zh="五边形 COF 纳米管中的热导率",
                summary_zh="这篇论文讨论五边形 COF 纳米管热导率。",
                reason_zh="与当前研究兴趣高度相关。",
                matched_topics=["热导率"],
            )
        ],
    )

    paths = write_digests(run, tmp_path, ["md", "html"])

    assert tmp_path / "2026-04-28-digest.md" in paths
    assert tmp_path / "2026-04-28-digest.html" in paths
    html = (tmp_path / "2026-04-28-digest.html").read_text(encoding="utf-8")
    assert "每日科研文献摘要" in html
    assert "data-filter=\"high\"" in html
    assert "type=\"search\"" in html
    assert "toc.png" in html
    assert "https://example.org/paper" in html

