# BCP comparison tools

## HTML crawler to Markdown

Use `crawler_to_markdown.py` to crawl one or more HTML pages, extract visible text, and emit Markdown.

### Usage

```bash
python3 crawler_to_markdown.py "The 1928 Book of Common Prayer_ Morning Prayer.html" -o morning_prayer.md
```

With a remote URL:

```bash
python3 crawler_to_markdown.py "https://example.com" --max-pages 10 -o site.md
```

By default, crawling is restricted to the same domain (or local directory for files). Use `--allow-external` to follow external links.
