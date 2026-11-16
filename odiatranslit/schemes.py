"""Letter tables for the three romanisation schemes.

ISO 15919 - academic transliteration with diacritics (reversible)
Hunterian - Government of India style, plain ASCII, lossy
ITRANS    - ASCII keyboard-friendly spelling (reversible)

Every table has the same shape:
    vowels      independent vowel  -> roman
    consonants  bare consonant     -> roman (without the inherent 'a')
    matras      vowel sign         -> roman (replaces the inherent 'a')
    modifiers   ଁ ଂ ଃ ଽ             -> roman
    schwa       the inherent vowel ('a' in all three schemes)

Adapted from OpenOdia:
https://github.com/soumendrak/openodia/blob/main/openodia/roman/_tables.py

Original project licensed under the MIT License.
Modified for use in this project.
"""

from __future__ import annotations

from typing import TypedDict


class SchemeTable(TypedDict):
    """Mapping table shared by all romanisation schemes.

    Each scheme defines the same five categories so that the transliteration
    code can use a common interface regardless of the selected scheme.

    Keys:
        schwa: Roman spelling of the inherent vowel carried by a consonant.
        vowels: Independent Odia vowels mapped to Roman spellings.
        consonants: Bare Odia consonants mapped to Roman spellings, without
            their inherent vowel.
        matras: Dependent Odia vowel signs mapped to Roman spellings.
        modifiers: Odia signs such as chandrabindu, anusvara, visarga, and
            avagraha mapped to Roman spellings.
    """

    schwa: str
    vowels: dict[str, str]
    consonants: dict[str, str]
    matras: dict[str, str]
    modifiers: dict[str, str]


# ---------------------------------------------------------------------------
# Special Odia letters
# ---------------------------------------------------------------------------

# These three letters are easy to confuse with ଡ/ଢ/ଯ followed by a nukta
# when entered or normalised. Use their Unicode code points explicitly so
# they remain distinct keys in the transliteration tables.
RRA = chr(0x0B5C)  # ଡ଼
RHA = chr(0x0B5D)  # ଢ଼
YYA = chr(0x0B5F)  # ୟ

# ---------------------------------------------------------------------------
# Combining marks used by ISO 15919
# ---------------------------------------------------------------------------

# Keep these marks explicit instead of relying on visually pre-composed
# characters. Some ISO 15919 spellings require a base Latin letter followed
# by one or more Unicode combining marks.
RING_BELOW = "\u0325"
MACRON = "\u0304"
CANDRABINDU = "\u0310"


# ---------------------------------------------------------------------------
# ISO 15919
# ---------------------------------------------------------------------------

# ISO 15919 distinguishes vowel length, retroflex consonants, nasal sounds,
# and other phonological distinctions with Latin diacritics. These
# distinctions make the mapping suitable for reversible transliteration.

# fmt: off
ISO15919: SchemeTable = {
    # Inherent vowel supplied by a consonant when no matra or halant follows.
    "schwa": "a",

    # Independent vowels.
    "vowels": {
        "ଅ": "a", "ଆ": "ā", "ଇ": "i", "ଈ": "ī", "ଉ": "u", "ଊ": "ū",
        "ଋ": "r" + RING_BELOW, "ଌ": "l" + RING_BELOW,
        "ୠ": "r" + RING_BELOW + MACRON, "ୡ": "l" + RING_BELOW + MACRON,
        "ଏ": "ē", "ଐ": "ai", "ଓ": "ō", "ଔ": "au",
    },

    # Bare consonants. The inherent "a" is intentionally omitted here;
    # it is supplied separately by the transliteration logic.
    "consonants": {
        "କ": "k", "ଖ": "kh", "ଗ": "g", "ଘ": "gh", "ଙ": "ṅ",
        "ଚ": "c", "ଛ": "ch", "ଜ": "j", "ଝ": "jh", "ଞ": "ñ",
        "ଟ": "ṭ", "ଠ": "ṭh", "ଡ": "ḍ", "ଢ": "ḍh", "ଣ": "ṇ",
        "ତ": "t", "ଥ": "th", "ଦ": "d", "ଧ": "dh", "ନ": "n",
        "ପ": "p", "ଫ": "ph", "ବ": "b", "ଭ": "bh", "ମ": "m",
        "ଯ": "y", "ର": "r", "ଲ": "l", "ଳ": "ḷ", "ଵ": "v", "ୱ": "w",
        "ଶ": "ś", "ଷ": "ṣ", "ସ": "s", "ହ": "h",
        RRA: "ṛ", RHA: "ṛh", YYA: "ẏ",
    },

    # Dependent vowel signs. A matra replaces the inherent vowel of the
    # consonant to which it is attached.
    "matras": {
        "ା": "ā", "ି": "i", "ୀ": "ī", "ୁ": "u", "ୂ": "ū",
        "ୃ": "r" + RING_BELOW, "ୄ": "r" + RING_BELOW + MACRON,
        "ୢ": "l" + RING_BELOW, "ୣ": "l" + RING_BELOW + MACRON,
        "େ": "ē", "ୈ": "ai", "ୋ": "ō", "ୌ": "au",
    },

    "modifiers": {"ଁ": "m" + CANDRABINDU, "ଂ": "ṁ", "ଃ": "ḥ", "ଽ": "\u2019"},
}


# ---------------------------------------------------------------------------
# Hunterian
# ---------------------------------------------------------------------------

# Hunterian uses plain ASCII and intentionally collapses distinctions that
# ISO 15919 preserves. Long and short vowels, retroflex/dental consonants,
# and several other Odia letters therefore share the same Roman spelling.
#
# Because different Odia characters can produce identical Roman output,
# Hunterian transliteration is lossy and reverse transliteration can only
# choose a preferred Odia character for an ambiguous spelling.
HUNTERIAN: SchemeTable = {
    "schwa": "a",

    # Vowel length is not preserved. For example, both ଅ/ଆ become "a",
    # ଇ/ଈ become "i", and ଉ/ଊ become "u".
    "vowels": {
        "ଅ": "a", "ଆ": "a", "ଇ": "i", "ଈ": "i", "ଉ": "u", "ଊ": "u",
        "ଋ": "ri", "ଌ": "li", "ୠ": "ri", "ୡ": "li",
        "ଏ": "e", "ଐ": "ai", "ଓ": "o", "ଔ": "au",
    },

    # Several consonants deliberately share a spelling. For example,
    # ଞ/ଣ/ନ -> "n", ଟ/ତ -> "t", ଡ/ଦ -> "d", and ଶ/ଷ -> "sh".
    "consonants": {
        "କ": "k", "ଖ": "kh", "ଗ": "g", "ଘ": "gh", "ଙ": "ng",
        "ଚ": "ch", "ଛ": "chh", "ଜ": "j", "ଝ": "jh", "ଞ": "n",
        "ଟ": "t", "ଠ": "th", "ଡ": "d", "ଢ": "dh", "ଣ": "n",
        "ତ": "t", "ଥ": "th", "ଦ": "d", "ଧ": "dh", "ନ": "n",
        "ପ": "p", "ଫ": "ph", "ବ": "b", "ଭ": "bh", "ମ": "m",
        "ଯ": "y", "ର": "r", "ଲ": "l", "ଳ": "l", "ଵ": "v", "ୱ": "w",
        "ଶ": "sh", "ଷ": "sh", "ସ": "s", "ହ": "h",
        RRA: "r", RHA: "rh", YYA: "y",
    },

    # As with the independent vowels, vowel length and some other
    # distinctions are intentionally discarded from dependent vowel signs.
    "matras": {
        "ା": "a", "ି": "i", "ୀ": "i", "ୁ": "u", "ୂ": "u",
        "ୃ": "ri", "ୄ": "ri", "ୢ": "li", "ୣ": "li",
        "େ": "e", "ୈ": "ai", "ୋ": "o", "ୌ": "au",
    },

    # Modifier spellings are also ambiguous in Hunterian. In particular,
    # chandrabindu and anusvara both become "n", while visarga becomes "h".
    "modifiers": {"ଁ": "n", "ଂ": "n", "ଃ": "h", "ଽ": "'"},
}

# ---------------------------------------------------------------------------
# ITRANS
# ---------------------------------------------------------------------------

# ITRANS represents Indic-script distinctions using ASCII combinations and
# letter case rather than Unicode diacritics. For example, long vowels use
# uppercase letters and retroflex consonants are distinguished from their
# dental equivalents by uppercase spellings.
#
# Unlike Hunterian, these distinctions provide enough information for
# reversible transliteration when the encoder's reversible mode is used.

ITRANS: SchemeTable = {
    "schwa": "a",

    # Independent vowels. Uppercase spellings distinguish long vowels,
    # while multi-character sequences represent vocalic r/l and diphthongs.
    "vowels": {
        "ଅ": "a", "ଆ": "A", "ଇ": "i", "ଈ": "I", "ଉ": "u", "ଊ": "U",
        "ଋ": "RRi", "ଌ": "LLi", "ୠ": "RRI", "ୡ": "LLI",
        "ଏ": "e", "ଐ": "ai", "ଓ": "o", "ଔ": "au",
    },

    # Bare consonants. Case and punctuation distinguish sounds that would
    # otherwise collide in ASCII, such as dental t/d and retroflex T/D.
    "consonants": {
        "କ": "k", "ଖ": "kh", "ଗ": "g", "ଘ": "gh", "ଙ": "~N",
        "ଚ": "ch", "ଛ": "Ch", "ଜ": "j", "ଝ": "jh", "ଞ": "~n",
        "ଟ": "T", "ଠ": "Th", "ଡ": "D", "ଢ": "Dh", "ଣ": "N",
        "ତ": "t", "ଥ": "th", "ଦ": "d", "ଧ": "dh", "ନ": "n",
        "ପ": "p", "ଫ": "ph", "ବ": "b", "ଭ": "bh", "ମ": "m",
        "ଯ": "y", "ର": "r", "ଲ": "l", "ଳ": "L", "ଵ": "v", "ୱ": "w",
        "ଶ": "sh", "ଷ": "Sh", "ସ": "s", "ହ": "h",
        RRA: ".D", RHA: ".Dh", YYA: "Y",
    },

    # Dependent vowel signs use the same Roman spellings as their
    # corresponding independent vowels.
    "matras": {
        "ା": "A", "ି": "i", "ୀ": "I", "ୁ": "u", "ୂ": "U",
        "ୃ": "RRi", "ୄ": "RRI", "ୢ": "LLi", "ୣ": "LLI",
        "େ": "e", "ୈ": "ai", "ୋ": "o", "ୌ": "au",
    },

    # ITRANS uses punctuation and uppercase letters to keep these modifier
    # spellings distinct from ordinary consonant and vowel sequences.
    "modifiers": {"ଁ": ".N", "ଂ": "M", "ଃ": "H", "ଽ": ".a"},
}
# fmt: on


TABLES: dict[str, SchemeTable] = {
    "ISO15919": ISO15919,
    "Hunterian": HUNTERIAN,
    "ITRANS": ITRANS,
}
