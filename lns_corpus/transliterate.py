from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
def devanagari_to_iast(text:str)->str:
    return transliterate(text,sanscript.DEVANAGARI,sanscript.IAST)
def devanagari_to_slp1(text:str)->str:
    return transliterate(text,sanscript.DEVANAGARI,sanscript.SLP1)
