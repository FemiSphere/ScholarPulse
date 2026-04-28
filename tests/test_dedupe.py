from literature_digest.dedupe import canonicalize_url, deduplicate_entries, normalize_title
from literature_digest.models import PaperEntry


def test_dedupe_by_doi_url_and_fuzzy_title():
    entries = [
        PaperEntry(title="Thermal transport in pentagonal COF nanotubes", doi="10.1000/ABC.1"),
        PaperEntry(title="Different title", doi="https://doi.org/10.1000/abc.1"),
        PaperEntry(title="Machine learning potentials for COFs", url="https://example.org/a?utm_source=x"),
        PaperEntry(title="Machine learning potentials for COFs", url="https://example.org/a"),
        PaperEntry(title="Pentagonal framework materials for thermal conductivity"),
        PaperEntry(title="Thermal conductivity of pentagonal framework materials"),
    ]

    result = deduplicate_entries(entries, fuzzy_title_threshold=80)

    assert result.duplicates_removed == 3
    assert len(result.unique_entries) == 3


def test_normalizers():
    assert normalize_title("  A Study: Thermal-Conductivity! ") == "a study thermal conductivity"
    assert canonicalize_url("HTTPS://Example.org/A/?utm_source=x&keep=1#frag") == "https://example.org/A?keep=1"

