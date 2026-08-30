DEVANAGARI_DIGITS = "०१२३४५६७८९"
ASCII_DIGITS = "0123456789"
_TRANS = str.maketrans(DEVANAGARI_DIGITS, ASCII_DIGITS)

def devanagari_to_ascii(text: str) -> str:
    return text.translate(_TRANS)
