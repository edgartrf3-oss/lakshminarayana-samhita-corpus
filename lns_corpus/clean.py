import html, re
COMMENT_RE=re.compile(r"<!--.*?-->",re.S)
REF_RE=re.compile(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>",re.S|re.I)
SIMPLE_TAG_RE=re.compile(r"</?(?:poem|div|span|p|br|center|small|big)[^>]*>",re.I)
CATEGORY_RE=re.compile(r"\[\[(?:Category|वर्ग):[^\]]+\]\]",re.I)
def conservative_wikitext_cleanup(text:str)->str:
    text=html.unescape(text); text=COMMENT_RE.sub("",text); text=REF_RE.sub("",text)
    text=SIMPLE_TAG_RE.sub("\n",text); text=CATEGORY_RE.sub("",text)
    text=text.replace("\r\n","\n").replace("\r","\n")
    return "\n".join(line.rstrip() for line in text.splitlines())
