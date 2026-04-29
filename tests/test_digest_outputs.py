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
                    venue="Journal of Thermal Transport, 2026",
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
    assert "科研文献摘要" in html
    assert "每日科研文献摘要" not in html
    assert 'data-filter="high"' in html
    assert 'type="search"' in html
    assert "Journal of Thermal Transport, 2026" in html
    assert "toc.png" in html
    assert "https://example.org/paper" in html
    assert "英文原题：Thermal conductivity in pentagonal COF nanotubes" in html


def test_digest_does_not_show_english_title_as_chinese_title(tmp_path):
    run = DigestRun(
        date_label="2026-04-28",
        stats=RunStats(paper_entries_extracted=1, low_relevance=1),
        interest_profile=InterestProfile(summary_zh="测试"),
        papers=[
            RankedPaper(
                entry=PaperEntry(title="Metal-modulated phonon transport in porphyrin-based MOFs"),
                relevance="low",
                score=0.0,
                title_zh="Metal-modulated phonon transport in porphyrin-based MOFs",
                summary_zh="LLM 未返回摘要。",
                reason_zh="LLM 未返回推荐理由。",
            )
        ],
    )

    paths = write_digests(run, tmp_path, ["md", "html"])
    markdown = (tmp_path / "2026-04-28-digest.md").read_text(encoding="utf-8")
    html = (tmp_path / "2026-04-28-digest.html").read_text(encoding="utf-8")

    assert tmp_path / "2026-04-28-digest.md" in paths
    assert "中文标题暂未生成" in markdown
    assert "英文原题：Metal-modulated phonon transport in porphyrin-based MOFs" in markdown
    assert "中文标题暂未生成" in html
    assert "英文原题：Metal-modulated phonon transport in porphyrin-based MOFs" in html


def test_write_digests_can_avoid_overwriting_existing_outputs(tmp_path):
    run = DigestRun(
        date_label="2026-04-28",
        stats=RunStats(),
        interest_profile=InterestProfile(summary_zh="测试"),
        papers=[],
    )
    existing_md = tmp_path / "2026-04-28-digest.md"
    existing_html = tmp_path / "2026-04-28-digest.html"
    existing_md.write_text("existing md", encoding="utf-8")
    existing_html.write_text("existing html", encoding="utf-8")

    paths = write_digests(run, tmp_path, ["md", "html"], overwrite_existing=False)

    assert tmp_path / "2026-04-28-digest-2.md" in paths
    assert tmp_path / "2026-04-28-digest-2.html" in paths
    assert existing_md.read_text(encoding="utf-8") == "existing md"
    assert existing_html.read_text(encoding="utf-8") == "existing html"
