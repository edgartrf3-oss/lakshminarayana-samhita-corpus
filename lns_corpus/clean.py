import html, re

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
REF_RE = re.compile(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", re.S | re.I)
SIMPLE_TAG_RE = re.compile(r"</?(?:poem|div|span|p|br|center|small|big)[^>]*>", re.I)
CATEGORY_RE = re.compile(r"\[\[(?:Category|वर्ग):[^\]]+\]\]", re.I)

# Sanskrit Wikisource chapter pages commonly begin with a MediaWiki `header`
# template containing title/navigation metadata.  It is interface boilerplate,
# not part of the LNS witness, and was previously buffered into the first
# segmented verse.  Remove only a leading header template; never strip general
# templates from the body, because those could carry textual information.
LEADING_HEADER_RE = re.compile(r"\A\s*\{\{\s*header\b.*?\}\}\s*", re.S | re.I)


def conservative_wikitext_cleanup(text: str) -> str:
    text = html.unescape(text)
    text = COMMENT_RE.sub("", text)
    text = REF_RE.sub("", text)
    text = SIMPLE_TAG_RE.sub("\n", text)
    text = CATEGORY_RE.sub("", text)
    text = LEADING_HEADER_RE.sub("", text, count=1)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines())
