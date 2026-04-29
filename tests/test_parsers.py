from pathlib import Path

from literature_digest.models import EmailMessage
from literature_digest.llm.base import extract_json_object
from literature_digest.parsers import parse_email, parse_emails


def test_google_scholar_alert_extracts_multiple_papers():
    email = EmailMessage(
        id="m1",
        thread_id="t1",
        subject="Google Scholar Alert",
        sender="Google Scholar Alerts <scholaralerts-noreply@google.com>",
        date=None,
        html="""
        <html><body>
          <a href="https://example.org/paper-a">Machine-learning interatomic potentials for thermal conductivity in COF nanotubes</a>
          <p>Authors - Journal, 2026. Phonon transport in framework materials.</p>
          <a href="https://example.org/paper-b">Pentagonal framework materials for low-dimensional heat transport</a>
          <p>Another relevant result.</p>
        </body></html>
        """,
    )

    entries = parse_email(email)

    assert len(entries) == 2
    assert entries[0].title.startswith("Machine-learning interatomic potentials")
    assert entries[0].url == "https://example.org/paper-a"


def test_google_scholar_alert_extracts_venue_and_skips_profile_links():
    email = EmailMessage(
        id="m1b",
        thread_id="t1",
        subject="Google Scholar Alert",
        sender="Google Scholar Alerts <scholaralerts-noreply@google.com>",
        date=None,
        html="""
        <html><body>
          <style>.gse_alrt_title{text-decoration:none}</style>
          <a href="https://scholar.google.com/scholar_url?url=https%3A%2F%2Fpubs.aip.org%2Faip%2Fapl%2Farticle%2F128%2F15%2F152202%2F3387245&hl=en">
            Metal-modulated phonon transport in porphyrin-based MOFs
          </a>
          <div>HL Kuang, H Tong, YJ Zeng, BY Huang, WX Zhou - Applied Physics Letters, 2026</div>
          <div>Metal centers in porphyrin-based frameworks induce distinct thermal transport behaviors.</div>
          <img src="https://scholar.google.com/intl/zh-CN/scholar/images/1x/save-32.png">
          <img src="https://scholar.google.com/intl/zh-CN/scholar/images/1x/tw-32.png">
          <a href="https://scholar.google.com/citations?hl=en&user=jD1qR3gAAAAJ">Wu-Xing Zhou (周五星)</a>
          <a href="https://scholar.google.com/scholar_alerts?view_op=cancel_alert_options">Cancel alert</a>
        </body></html>
        """,
    )

    entries = parse_email(email)

    assert len(entries) == 1
    assert entries[0].url == "https://pubs.aip.org/aip/apl/article/128/15/152202/3387245"
    assert entries[0].venue == "Applied Physics Letters, 2026"
    assert entries[0].image_paths == []


def test_keyword_google_scholar_alert_skips_search_query_link():
    email = EmailMessage(
        id="m1c",
        thread_id="t1",
        subject='covalent organic framework, "thermal conductivity" - 新的结果',
        sender="Google 学术搜索快讯 <scholaralerts-noreply@google.com>",
        date=None,
        html="""
        <html><body>
          <a href="https://scholar.google.com/scholar_url?url=https%3A%2F%2Fwww.sciencedirect.com%2Fscience%2Farticle%2Fpii%2FS0169433225025760&hl=zh-CN">
            HKUST-1 assisted liquid metal in constructing polydimethylsiloxane-based composites for improving thermal conductivity
          </a>
          <div>Y Liu, X Wang - Applied Surface Science, 2025</div>
          <a href="https://scholar.google.com/scholar?q=covalent+organic+framework,++%22thermal+conductivity%22&as_sdt=0,5&scisbd=1&hl=zh-CN">
            [covalent organic framework, "thermal conductivity"]
          </a>
        </body></html>
        """,
    )

    entries = parse_email(email)

    assert len(entries) == 1
    assert entries[0].venue == "Applied Surface Science, 2025"
    assert entries[0].image_paths == []


def test_journal_toc_keeps_image_references():
    image_path = Path("data/toc_images/2026-04-28/toc.png")
    email = EmailMessage(
        id="m2",
        thread_id="t2",
        subject="Journal TOC",
        sender="alerts@journal.example",
        date=None,
        html="""
        <html><body>
          <img src="cid:toc-image">
          <a href="https://doi.org/10.1234/example.001">Phonon-limited thermal conductivity in framework nanotubes</a>
        </body></html>
        """,
        image_paths=[image_path],
    )

    entries = parse_email(email)

    assert len(entries) == 1
    assert entries[0].doi == "10.1234/example.001"
    assert entries[0].image_paths == [image_path]


def test_text_email_extracts_doi_url_and_title_candidate():
    email = EmailMessage(
        id="m3",
        thread_id="t3",
        subject="RSS alert",
        sender="rss@example.org",
        date=None,
        text="""
        Machine learning potentials reveal thermal transport in pentagonal materials
        https://example.org/rss-paper
        DOI: 10.5678/rss.2026.42
        """,
    )

    entries = parse_email(email)

    assert len(entries) >= 1
    assert entries[0].doi == "10.5678/rss.2026.42"
    assert entries[0].url == "https://example.org/rss-paper"


class StructuredEmailClient:
    def complete(self, prompt: str) -> str:
        assert "EMAIL_PAPER_EXTRACTION_JSON" in prompt
        assert "Visit our Email Preference Center" in prompt
        return """
        {
          "papers": [
            {
              "title": "Anisotropic Thermal Conductivity Enhancement of the Aligned Metal-Organic Framework under Water Vapor Adsorption",
              "url": "https://pubs.acs.org/doi/10.1021/acs.jpclett.4c01244",
              "doi": "10.1021/acs.jpclett.4c01244",
              "venue": "The Journal of Physical Chemistry Letters",
              "authors": "Shingi Yamaguchi, Junichiro Shiomi, et al.",
              "snippet": "Publication Date (Web): June 18, 2024",
              "image_index": 0
            }
          ]
        }
        """

    def complete_json(self, prompt: str):
        return extract_json_object(self.complete(prompt))


def test_non_scholar_email_can_use_llm_structuring_and_skip_footer_links():
    email = EmailMessage(
        id="acs",
        thread_id="t",
        subject="Recommended Reading from ACS Publications",
        sender="ACS Recommended Reading <updates@acspubs.org>",
        date=None,
        html="""
        <html><body>
          <p>The Journal of Physical Chemistry Letters</p>
          <img src="https://app.acspubs.org/e/FooterImages/FooterImage1?x=1">
          <img src="https://pubs.acs.org/cms/10.1021/acs.jpclett.4c01244/asset/images/medium/jz4c01244_0005.gif">
          <a href="https://pubs.acs.org/doi/10.1021/acs.jpclett.4c01244">
            Anisotropic Thermal Conductivity Enhancement of the Aligned Metal-Organic Framework under Water Vapor Adsorption
          </a>
          <a href="https://pubs.acs.org/doi/10.1021/acs.jpclett.4c01244">DOI: 10.1021/acs.jpclett.4c01244</a>
          <a href="https://preferences.acs.org/">Visit our Email Preference Center</a>
          <a href="https://preferences.acs.org/unsubscribe/all">Stop all emails from ACS Publications</a>
        </body></html>
        """,
    )

    entries = parse_emails(
        [email],
        llm=StructuredEmailClient(),
        llm_structure_non_scholar=True,
    )

    assert len(entries) == 1
    assert entries[0].venue == "The Journal of Physical Chemistry Letters"
    assert entries[0].doi == "10.1021/acs.jpclett.4c01244"
    assert entries[0].image_paths == [
        "https://pubs.acs.org/cms/10.1021/acs.jpclett.4c01244/asset/images/medium/jz4c01244_0005.gif"
    ]
