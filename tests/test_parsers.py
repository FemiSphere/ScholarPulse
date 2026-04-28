from pathlib import Path

from literature_digest.models import EmailMessage
from literature_digest.parsers import parse_email


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

