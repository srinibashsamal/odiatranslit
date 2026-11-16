"""Odia <-> Roman transliteration (ISO 15919, Hunterian, ITRANS)."""

from ._engine import SCHEMES, Scheme
from .api import (
    from_hunterian,
    from_iso15919,
    from_itrans,
    from_roman,
    to_hunterian,
    to_iso15919,
    to_itrans,
    to_roman,
    transliterate,
)
from .schemes import TABLES, SchemeTable

__version__ = "0.1.0"

__all__ = [
    "SCHEMES",
    "TABLES",
    "Scheme",
    "SchemeTable",
    "__version__",
    "from_hunterian",
    "from_iso15919",
    "from_itrans",
    "from_roman",
    "to_hunterian",
    "to_iso15919",
    "to_itrans",
    "to_roman",
    "transliterate",
]
