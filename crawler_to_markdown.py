#!/usr/bin/env python3
"""Crawl HTML pages and convert extracted text content into Markdown."""

from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen


def decode_html(raw: bytes, content_type: str) -> str:
    """Decode HTML bytes using header/meta charset hints with safe fallbacks."""
    charset_match = re.search(r"charset=([\w\-]+)", content_type, flags=re.IGNORECASE)
    encodings: list[str] = []
    if charset_match:
        encodings.append(charset_match.group(1).strip('"\''))

    head = raw[:4096].decode("ascii", errors="ignore")
    meta_match = re.search(
        r"<meta[^>]+charset\s*=\s*[\"']?([\w\-]+)", head, flags=re.IGNORECASE
    )
    if meta_match:
        encodings.append(meta_match.group(1))

    encodings.extend(["utf-8", "windows-1252", "latin-1"])

    seen: set[str] = set()
    for enc in encodings:
        normalized = enc.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue

    return raw.decode("utf-8", errors="replace")


def normalize_caps_spacing(text: str) -> str:
    """Fix odd OCR/small-caps spacing artifacts in extracted text."""

    def merge_split_caps(match: re.Match[str]) -> str:
        first, rest = match.group(1), match.group(2)
        if (first, rest) in {("O", "LORD"), ("O", "GOD"), ("I", "BELIEVE")}:
            return f"{first} {rest}"
        return f"{first}{rest}"

    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\b([A-Z])\s+([A-Z]{2,})\b", merge_split_caps, text)
        text = re.sub(r"\bW\s+E\b", "WE", text)
        text = re.sub(r"\bOL\s+ORD\b", "O LORD", text)

    return text


SECTION_TITLE_PATTERNS = [
    re.compile(r"^A General Confession\.$"),
    re.compile(r"^A General Thanksgiving\.$"),
    re.compile(r"^The Declaration of Absolution, or Remission of Sins\.$"),
    re.compile(r"^Venite, exultemus Domino\.$"),
    re.compile(r"^Te Deum laudamus\.$"),
    re.compile(r"^Benedictus es Domine\.$"),
    re.compile(r"^Benedictus\. St\. Luke i\. 68\.$"),
    re.compile(r"^Jubilate Deo\. Psalm c\.$"),
    re.compile(r"^A Collect for .+\.$"),
    re.compile(r"^A Prayer for .+\.$"),
    re.compile(r"^A Prayer of St\. Chrysostom\.$"),
    re.compile(r"^The Order for Daily Morning Prayer\.$", re.IGNORECASE),
]


def is_section_title(line: str) -> bool:
    if not line or line.startswith(("#", "¶", ">", "-", "[", "*")):
        return False
    if any(pat.match(line) for pat in SECTION_TITLE_PATTERNS):
        return True
    # Preserve the broad section heading in this source.
    if line in {"THE ORDER FOR", "DAILY MORNING PRAYER."}:
        return True
    return False


def style_section_titles(markdown: str) -> str:
    styled: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if is_section_title(stripped):
            styled.append(f"***{stripped}***")
        else:
            styled.append(line)
    return "\n".join(styled)


BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
}
HEADING_TAGS = {f"h{i}" for i in range(1, 7)}


class LinkExtractor(HTMLParser):
    """Extract hyperlinks from an HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


class MarkdownTextExtractor(HTMLParser):
    """Extract visible text and format it as light Markdown."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.tag_stack: list[str] = []
        self.link_href_stack: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_stack.append(tag)

        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        if tag == "br":
            self.parts.append("\n")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")
            if tag in HEADING_TAGS:
                level = int(tag[1])
                self.parts.append(f"{'#' * level} ")
            elif tag == "li":
                self.parts.append("- ")
            elif tag == "blockquote":
                self.parts.append("> ")

        if tag == "a":
            href = ""
            for key, value in attrs:
                if key == "href" and value:
                    href = value
                    break
            self.link_href_stack.append(href)
            self.parts.append("[")

    def handle_endtag(self, tag: str) -> None:
        if self.tag_stack:
            self.tag_stack.pop()

        if tag in {"script", "style", "noscript"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_depth > 0:
            return

        if tag == "a":
            href = self.link_href_stack.pop() if self.link_href_stack else ""
            if href:
                self.parts.append(f"]({href})")
            else:
                self.parts.append("]")

        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        cleaned = normalize_caps_spacing(cleaned)
        if cleaned:
            if cleaned.startswith("¶"):
                cleaned = f"¶ {cleaned.lstrip('¶').strip()}"
            self.parts.append(cleaned + " ")

    def markdown(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"[ \t]+\n", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        raw = normalize_caps_spacing(raw)
        raw = re.sub(r"\s+([,.;:?!])", r"\1", raw)
        raw = style_section_titles(raw)
        return raw.strip() + "\n"


@dataclass
class Page:
    url: str
    markdown: str


def normalize_url(base_url: str, link: str) -> str:
    absolute = urldefrag(urljoin(base_url, link))[0]
    return absolute


def is_same_scope(seed: str, candidate: str) -> bool:
    seed_parsed = urlparse(seed)
    cand_parsed = urlparse(candidate)

    if seed_parsed.scheme == "file":
        seed_root = str(Path(seed_parsed.path).parent.resolve())
        cand_path = Path(cand_parsed.path).resolve()
        return str(cand_path).startswith(seed_root)

    return seed_parsed.netloc == cand_parsed.netloc


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "markdown-crawler/1.0"})
    with urlopen(request, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type and not url.lower().endswith((".html", ".htm")):
            return ""
        raw = response.read()
        return decode_html(raw, content_type)


def extract_links(base_url: str, html: str) -> list[str]:
    extractor = LinkExtractor()
    extractor.feed(html)
    return [normalize_url(base_url, href) for href in extractor.links]


def html_to_markdown(html: str) -> str:
    parser = MarkdownTextExtractor()
    parser.feed(html)
    return parser.markdown()


def crawl(seed: str, max_pages: int = 25, same_scope: bool = True) -> list[Page]:
    queue = deque([seed])
    visited: set[str] = set()
    pages: list[Page] = []

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            html = fetch_text(url)
        except Exception:
            continue

        if not html:
            continue

        markdown = html_to_markdown(html)
        pages.append(Page(url=url, markdown=markdown))

        for link in extract_links(url, html):
            if link in visited:
                continue
            if same_scope and not is_same_scope(seed, link):
                continue
            if urlparse(link).scheme not in {"http", "https", "file"}:
                continue
            queue.append(link)

    return pages


def ensure_file_url(path_or_url: str) -> str:
    parsed = urlparse(path_or_url)
    if parsed.scheme in {"http", "https", "file"}:
        return path_or_url
    return Path(path_or_url).resolve().as_uri()


def combine_markdown(pages: Iterable[Page]) -> str:
    sections = []
    for page in pages:
        title = f"# Source: {page.url}"
        sections.append(f"{title}\n\n{page.markdown}".strip())
    return "\n\n---\n\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl HTML pages and convert extracted text into Markdown."
    )
    parser.add_argument("source", help="Seed URL or local HTML file path")
    parser.add_argument(
        "-o",
        "--output",
        default="output.md",
        help="Output Markdown file path (default: output.md)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=25, help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow crawling links outside the source domain/directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed = ensure_file_url(args.source)
    pages = crawl(seed, max_pages=args.max_pages, same_scope=not args.allow_external)
    markdown = combine_markdown(pages)
    Path(args.output).write_text(markdown, encoding="utf-8")
    print(f"Wrote {len(pages)} page(s) to {args.output}")


if __name__ == "__main__":
    main()
