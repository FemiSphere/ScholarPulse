from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Iterable

from .dedupe import DOI_RE, normalize_doi
from .models import EmailMessage, PaperEntry


URL_RE = re.compile(r"https?://[^\s<>)\"']+", re.IGNORECASE)
BAD_LINK_TEXT = {
    "pdf",
    "html",
    "view article",
    "read more",
    "full text",
    "unsubscribe",
    "manage alerts",
    "settings",
    "click here",
    "view online",
}


class _AnchorExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.images: list[str] = []
        self._href_stack: list[str] = []
        self._text_stack: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "a":
            self._href_stack.append(attrs_dict.get("href", ""))
            self._text_stack.append([])
        elif tag.lower() == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.images.append(src)

    def handle_data(self, data: str) -> None:
        if self._text_stack:
            self._text_stack[-1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href_stack:
            return
        href = self._href_stack.pop()
        pieces = self._text_stack.pop()
        text = normalize_space(" ".join(pieces))
        if href and text:
            self.links.append((href, text))


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html or "")
    return normalize_space("\n".join(parser.parts))


def parse_emails(emails: Iterable[EmailMessage]) -> list[PaperEntry]:
    entries: list[PaperEntry] = []
    for email in emails:
        entries.extend(parse_email(email))
    return entries


def parse_email(email: EmailMessage) -> list[PaperEntry]:
    if email.html:
        entries = _parse_html_email(email)
    else:
        entries = []
    if email.text and not entries:
        entries.extend(_parse_text_email(email))
    elif not email.html and email.snippet:
        entries.extend(_parse_text_email(email))
    return _dedupe_within_email(entries)


def _parse_html_email(email: EmailMessage) -> list[PaperEntry]:
    extractor = _AnchorExtractor()
    extractor.feed(email.html)
    text = html_to_text(email.html)
    entries: list[PaperEntry] = []
    image_refs = list(email.image_paths) + [src for src in extractor.images if _is_useful_image_src(src)]

    for href, link_text in extractor.links:
        title = normalize_space(link_text)
        if not _is_likely_title(title, href):
            continue
        raw = _snippet_around(text, title)
        entries.append(
            PaperEntry(
                title=title,
                url=_clean_url(href),
                abstract=raw,
                doi=normalize_doi(href + " " + raw),
                source_email_id=email.id,
                source_subject=email.subject,
                source_sender=email.sender,
                image_paths=image_refs,
                raw_text=raw,
            )
        )
    return entries


def _parse_text_email(email: EmailMessage) -> list[PaperEntry]:
    text = email.text or email.snippet
    if not text:
        return []
    urls = URL_RE.findall(text)
    dois = DOI_RE.findall(text)
    candidates = _title_candidates_from_text(text)
    entries: list[PaperEntry] = []

    for idx, title in enumerate(candidates[:12]):
        url = urls[idx] if idx < len(urls) else (urls[0] if len(candidates) == 1 and urls else "")
        doi = dois[idx] if idx < len(dois) else (dois[0] if len(candidates) == 1 and dois else "")
        entries.append(
            PaperEntry(
                title=title,
                url=_clean_url(url),
                abstract=_snippet_around(text, title),
                doi=normalize_doi(doi),
                source_email_id=email.id,
                source_subject=email.subject,
                source_sender=email.sender,
                image_paths=list(email.image_paths),
                raw_text=text[:2000],
            )
        )
    return entries


def _title_candidates_from_text(text: str) -> list[str]:
    candidates: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_space(raw_line)
        if not _is_likely_title(line, ""):
            continue
        candidates.append(line)
    if candidates:
        return candidates

    sentences = re.split(r"(?<=[.!?])\s+", normalize_space(text))
    return [sentence for sentence in sentences if _is_likely_title(sentence, "")][:8]


def _is_likely_title(text: str, href: str) -> bool:
    normalized = normalize_space(text)
    lower = normalized.lower()
    if len(normalized) < 16 or len(normalized) > 260:
        return False
    if lower in BAD_LINK_TEXT:
        return False
    if any(token in lower for token in ("unsubscribe", "privacy policy", "manage alert", "view online")):
        return False
    if lower.startswith(("http://", "https://", "doi:")):
        return False
    if href.lower().startswith(("mailto:", "#")):
        return False
    word_count = len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", normalized))
    return word_count >= 3


def _snippet_around(text: str, title: str, radius: int = 500) -> str:
    collapsed = normalize_space(text)
    idx = collapsed.lower().find(title.lower())
    if idx == -1:
        return collapsed[:radius]
    start = max(0, idx - radius // 3)
    end = min(len(collapsed), idx + len(title) + radius)
    return collapsed[start:end]


def _clean_url(url: str) -> str:
    return unescape(url or "").rstrip(".,;)\"'")


def _is_useful_image_src(src: str) -> bool:
    lower = src.lower().strip()
    if not lower:
        return False
    if any(token in lower for token in ("spacer", "tracking", "pixel", "logo", "icon")):
        return False
    return lower.startswith(("http://", "https://", "data/", "data:image", "./", "../")) or "." in lower


def _dedupe_within_email(entries: list[PaperEntry]) -> list[PaperEntry]:
    seen: set[tuple[str, str]] = set()
    result: list[PaperEntry] = []
    for entry in entries:
        key = (entry.title.lower(), entry.url.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result
