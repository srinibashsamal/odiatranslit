"""Internal Odia <-> Roman transliteration engine.

Public functions live in ``api.py`` and are re-exported at package level.

Adapted from OpenOdia:
https://github.com/soumendrak/openodia/blob/main/openodia/roman/_roman.py

Original project licensed under the MIT License.
Modified for use in this project.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cache
from typing import Literal

from .schemes import TABLES, SchemeTable

Scheme = Literal["ISO15919", "Hunterian", "ITRANS"]
SCHEMES: tuple[Scheme, ...] = ("ISO15919", "Hunterian", "ITRANS")

HALANT = "୍"
NUKTA = "\u0b3c"

# How each scheme writes a nukta. Hunterian drops it.
NUKTA_MARKS: dict[Scheme, str] = {
    "ISO15919": "\u00b7",
    "Hunterian": "",
    "ITRANS": "`",
}

# Separator used to split tokens that would otherwise merge,
# e.g. କଇ -> "ka:i" instead of "kai", which reads as କୈ.
# Hunterian has no separator, which is one reason it cannot round-trip.
SEPARATORS: dict[Scheme, str] = {
    "ISO15919": ":",
    "ITRANS": "_",
}

# Internal sentinel used only while encoding. It is never emitted in the
# final Roman string; _join_tokens turns it into a separator when needed.
HALANT_MARK = "\x00halant"

ODIA_RUN: re.Pattern[str] = re.compile("[\u0b00-\u0b7f]+")
ODIA_DIGITS: dict[int, int] = str.maketrans("୦୧୨୩୪୫୬୭୮୯", "0123456789")

# When a Hunterian spelling is ambiguous we deliberately choose the most
# frequent Odia letter so that the common case is recovered. This is a
# best-effort heuristic, not a reversible mapping.
HUNTERIAN_PREFERRED: dict[str, str] = {
    "n": "ନ",
    "t": "ତ",
    "th": "ଥ",
    "d": "ଦ",
    "dh": "ଧ",
}

# Alternative ITRANS spellings commonly entered by users.
ITRANS_ALIASES: dict[str, str] = {
    "aa": "A",
    "ii": "I",
    "uu": "U",
    "R^i": "RRi",
    "R^I": "RRI",
    "L^i": "LLi",
    "L^I": "LLI",
}


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ReverseIndex:
    """Precomputed reverse-transliteration lookup data.

    Attributes:
        tokens: Recognised Roman tokens sorted longest-first.
        by_first: Recognised tokens grouped by their first character.
        entries: Roman token to ``(kind, Odia character)`` mappings.
        max_len: Length of the longest recognised token.
        token_chars: Characters appearing in any recognised token.
    """

    tokens: tuple[str, ...]
    by_first: dict[str, tuple[str, ...]]
    entries: dict[str, tuple[str, str]]
    max_len: int
    token_chars: frozenset[str]


@dataclass
class _Encoder:
    """Walk Odia text one character at a time and collect Roman tokens.

    ``literal[i]`` records whether ``out[i]`` is passed-through text
    rather than a transliterated token.
    """

    table: SchemeTable
    scheme: Scheme
    sep: str | None
    escape: bool
    out: list[str] = field(default_factory=list)
    literal: list[bool] = field(default_factory=list)
    pending_schwa: bool = False  # last consonant still owes its inherent 'a'
    after_halant: bool = False

    def emit(self, token: str, is_literal: bool = False) -> None:
        """Append a Roman token and record whether it is literal text."""
        self.out.append(token)
        self.literal.append(is_literal)

    def flush_schwa(self) -> None:
        """Emit the inherent vowel owed by the preceding consonant."""
        if self.pending_schwa:
            self.emit(self.table["schwa"])
            self.pending_schwa = False

    def feed(self, ch: str) -> None:
        """Consume one prepared input character."""
        halant_before = self.after_halant
        self.after_halant = False

        if ch in self.table["consonants"]:
            self.flush_schwa()
            self.emit(self.table["consonants"][ch])
            self.pending_schwa = True

        elif ch in self.table["vowels"]:
            self.flush_schwa()
            if halant_before:
                self.emit(HALANT_MARK)
            self.emit(self.table["vowels"][ch])

        elif ch in self.table["matras"] or ch == HALANT:
            self._feed_sign(ch, halant_before)

        elif ch == NUKTA:
            self.emit(NUKTA_MARKS[self.scheme])

        else:
            self.flush_schwa()
            if ch in self.table["modifiers"]:
                self.emit(self.table["modifiers"][ch])
            elif self.escape and ch == self.sep:
                self.emit(ch * 2, is_literal=True)
            else:
                self.emit(ch, is_literal=True)

    def _feed_sign(self, ch: str, halant_before: bool) -> None:
        """Consume a halant or dependent vowel sign."""
        # A stray vowel sign or halant (no preceding consonant) cannot be
        # romanized directly: in reversible mode preserve it as literal text;
        # in non-reversible mode drop stray halants and emit matras as vowels.
        if self.escape and not self.pending_schwa:
            self.emit(ch, is_literal=True)
        elif ch == HALANT:
            self.after_halant = self.pending_schwa or halant_before
            self.pending_schwa = False
        else:
            self.emit(self.table["matras"][ch])
            self.pending_schwa = False


@dataclass
class _Decoder:
    """Read Roman text left-to-right using longest-match tokenization."""

    text: str
    by_first: dict[str, tuple[str, ...]]
    entries: dict[str, tuple[str, str]]
    matras: dict[str, str]
    schwa: str
    sep: str | None
    out: list[str] = field(default_factory=list)
    i: int = 0
    after_consonant: bool = False
    prev_was_token: bool = False

    def close_consonant(self) -> None:
        """Append a halant if a consonant is still open."""
        if self.after_consonant:
            self.out.append(HALANT)
            self.after_consonant = False

    def step(self) -> None:
        """Consume the next quoted section, separator, token, or literal."""
        if self._escaped_sep() or self._quoted():
            return

        match = self._match_at(self.i)
        if match is not None:
            self.prev_was_token = True
            self._read_token(match)
        elif not self._boundary():
            self.prev_was_token = False
            self.close_consonant()
            self.out.append(self.text[self.i])
            self.i += 1

    def _match_at(self, pos: int) -> str | None:
        """Return the longest recognised token starting at ``pos``."""
        if pos >= len(self.text):
            return None

        candidates = self.by_first.get(self.text[pos], ())
        return next(
            (token for token in candidates if self.text.startswith(token, pos)),
            None,
        )

    def _escaped_sep(self) -> bool:
        """Handle '::' / '__' -> literal separator."""
        sep = self.sep
        if sep is None or not self.text.startswith(sep * 2, self.i):
            return False

        self.close_consonant()
        self.out.append(sep)
        self.i += 2 * len(sep)
        self.prev_was_token = False
        return True

    def _quoted(self) -> bool:
        """Handle ':{...:}' / '_{..._}' -> copy the interior as-is."""
        sep = self.sep
        if sep is None or not self.text.startswith(sep + "{", self.i):
            return False

        start = self.i + len(sep) + 1
        end = self.text.find(sep + "}", start)
        if end == -1:
            return False

        self.close_consonant()
        self.out.append(self.text[start:end])
        self.i = end + len(sep) + 1
        self.prev_was_token = False
        return True

    def _boundary(self) -> bool:
        """Skip a separator that sits between two tokens, e.g. ':' in 'ka:i'."""
        sep = self.sep
        if sep is None or not self.prev_was_token:
            return False
        if not self.text.startswith(sep, self.i):
            return False

        start = self.i + len(sep)
        nxt = self._match_at(start)
        if nxt is None:
            return False

        self.i = start
        if self.entries[nxt][0] == "vowel":
            self.close_consonant()

        return True

    def _read_token(self, match: str) -> None:
        """Decode one recognised Roman token."""
        kind, odia = self.entries[match]
        self.i += len(match)

        if kind == "nukta":
            self.out.append(odia)

        elif kind == "vowel" and self.after_consonant:
            # The inherent "a" needs no explicit vowel sign.
            if match != self.schwa:
                self.out.append(self.matras.get(match, odia))
            self.after_consonant = False

        else:
            self.close_consonant()
            self.out.append(odia)
            self.after_consonant = kind == "consonant"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _get_table(scheme: Scheme) -> SchemeTable:
    """Return the table for a supported romanization scheme."""
    try:
        return TABLES[scheme]
    except KeyError:
        raise ValueError(f"unknown scheme {scheme!r}; supported: {SCHEMES}") from None


def _nfc_odia(text: str) -> str:
    """Normalise only the Odia runs; leave everything else unchanged."""
    return ODIA_RUN.sub(
        lambda match: unicodedata.normalize("NFC", match.group()),
        text,
    )


def _first_wins(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    """Invert odia -> roman pairs, keeping the first letter for a shared spelling."""
    result: dict[str, str] = {}

    for odia, roman in pairs:
        result.setdefault(roman, odia)

    return result


def _is_consonant_plus_vowel(
    spelling: str,
    consonants: dict[str, str],
    entries: dict[str, tuple[str, str]],
) -> bool:
    """Return True if a vowel spelling can also be read as consonant + vowel.

    Used only for Hunterian, where vowels such as "ri" and "li" can also be
    read as consonant + vowel.
    """
    if entries[spelling][0] != "vowel":
        return False

    return any(
        spelling[:cut] in consonants
        and entries.get(spelling[cut:], ("",))[0] == "vowel"
        for cut in range(1, len(spelling))
    )


@cache
def _reverse_index(scheme: Scheme) -> _ReverseIndex:
    """Build and cache the longest-match index used by the decoder.

    The returned structure contains:

    - recognised tokens sorted longest-first, so ``kh`` wins over ``k``;
    - a first-character index for candidate filtering;
    - Roman token to ``(kind, Odia character)`` mappings;
    - the length of the longest token; and
    - all characters used by recognised tokens.
    """
    table = _get_table(scheme)
    entries: dict[str, tuple[str, str]] = {}

    # When several Odia letters share a Roman spelling we keep the first one
    # encountered. Order therefore matters for reverse transliteration.
    for roman, odia in _first_wins(table["modifiers"].items()).items():
        entries[roman] = ("modifier", odia)

    for roman, odia in _first_wins(table["vowels"].items()).items():
        entries[roman] = ("vowel", odia)

    if NUKTA_MARKS[scheme]:
        entries[NUKTA_MARKS[scheme]] = ("nukta", NUKTA)

    consonants = _first_wins(table["consonants"].items())

    if scheme == "Hunterian":
        consonants.update(HUNTERIAN_PREFERRED)

        ambiguous = [
            roman
            for roman in entries
            if _is_consonant_plus_vowel(roman, consonants, entries)
        ]
        for roman in ambiguous:
            del entries[roman]

    for roman, odia in consonants.items():
        entries[roman] = ("consonant", odia)

    if scheme == "ITRANS":
        for alias, canonical in ITRANS_ALIASES.items():
            entries[alias] = entries[canonical]

    # Longest first, so "kh" is tried before "k".
    tokens = tuple(sorted(entries, key=len, reverse=True))

    grouped: dict[str, list[str]] = defaultdict(list)
    for token in tokens:
        grouped[token[0]].append(token)

    by_first = {
        first: tuple(grouped_tokens) for first, grouped_tokens in grouped.items()
    }

    max_len = len(tokens[0]) if tokens else 0
    token_chars = frozenset("".join(tokens))

    return _ReverseIndex(tokens, by_first, entries, max_len, token_chars)


# ---------------------------------------------------------------------------
# Odia -> Roman helpers
# ---------------------------------------------------------------------------


def _prepare(text: str, scheme: Scheme, reversible: bool) -> str:
    """Prepare text for Odia-to-Roman encoding.

    - Converts Odia digits to ASCII when the scheme requires it.
    - NFC-normalises Odia runs.
    - Re-joins ଡ଼ / ଢ଼ so they receive their dedicated spellings.
    """
    # In reversible ITRANS an ASCII digit would be ambiguous,
    # so Odia digits are only converted when a round-trip is not required.
    if scheme == "Hunterian" or (scheme == "ITRANS" and not reversible):
        text = text.translate(ODIA_DIGITS)

    text = _nfc_odia(text)

    # NFC splits ଡ଼/ଢ଼ into base + nukta; join them back so they get
    # their own spelling instead of "ḍ·".
    text = text.replace("ଡ" + NUKTA, chr(0x0B5C))
    return text.replace("ଢ" + NUKTA, chr(0x0B5D))


def _is_stable_space(ch: str) -> bool:
    """Return True if ``ch`` is whitespace that NFC will not alter."""
    # U+2000 and U+2001 are whitespace but NFC changes them.
    return ch.isspace() and unicodedata.normalize("NFC", ch) == ch


def _quote_literals(
    tokens: list[str],
    literal: list[bool],
    scheme: Scheme,
) -> tuple[list[str], list[bool]]:
    """Wrap passed-through text that the decoder could misinterpret.

    Without this, "କi" would become "kai" and decode as କୈ.
    A run of literal characters is quoted as ``:{run:}`` when it contains
    a letter used by the scheme, a combining mark, or anything NFC would change.
    """
    sep = SEPARATORS[scheme]
    token_chars = _reverse_index(scheme).token_chars

    new_tokens: list[str] = []
    new_literal: list[bool] = []
    run: list[str] = []

    def close_run() -> None:
        if not run:
            return

        chunk = "".join(run)
        needs_quote = bool(
            token_chars.intersection(chunk)
            or any(unicodedata.combining(char) for char in chunk)
            or unicodedata.normalize("NFC", chunk) != chunk
        )

        new_tokens.append(f"{sep}{{{chunk}{sep}}}" if needs_quote else chunk)
        new_literal.append(True)
        run.clear()

    for token, is_literal in zip(tokens, literal):
        if (
            is_literal
            and len(token) == 1
            and token != sep
            and not _is_stable_space(token)
        ):
            run.append(token)
            continue

        close_run()
        new_tokens.append(token)
        new_literal.append(is_literal)

    close_run()

    return new_tokens, new_literal


def _join_tokens(
    tokens: list[str],
    scheme: Scheme,
    literal: list[bool] | None = None,
) -> str:
    """Join tokens, inserting a separator where two of them would merge.

    Examples:
        କଇ  -> "ka:i"  (not "kai" = କୈ)
        କ୍ହ -> "k:ha"  (not "kha" = ଖ)

    Literal text is never split.
    """
    sep = SEPARATORS.get(scheme)
    if sep is None:
        return "".join(token for token in tokens if token != HALANT_MARK)

    if literal is None:
        literal = [False] * len(tokens)

    rev = _reverse_index(scheme)
    out: list[str] = []

    for i, token in enumerate(tokens):
        if token == HALANT_MARK:
            out.append(sep)
            continue

        out.append(token)

        nxt = i + 1
        if (
            literal[i]
            or nxt >= len(tokens)
            or literal[nxt]
            or tokens[nxt] == HALANT_MARK
            or not token
            or len(token) >= rev.max_len
        ):
            continue

        # Collect enough following characters to see whether token + what
        # follows starts with a longer token the decoder would grab instead.
        following: list[str] = []
        following_len = 0

        for j in range(nxt, len(tokens)):
            if literal[j] or tokens[j] == HALANT_MARK:
                break

            following.append(tokens[j])
            following_len += len(tokens[j])

            if len(token) + following_len >= rev.max_len:
                break

        joined = token + "".join(following)
        candidates = rev.by_first.get(token[0], ())

        if any(
            len(candidate) > len(token)
            and candidate.startswith(token)
            and joined.startswith(candidate)
            for candidate in candidates
        ):
            out.append(sep)

    return "".join(out)


# ---------------------------------------------------------------------------
# Roman -> Odia helpers
# ---------------------------------------------------------------------------


def _nfc_outside_quotes(text: str, sep: str) -> str:
    """NFC-normalise ``text`` while leaving ``:{...:}`` quoted parts untouched."""
    parts: list[str] = []
    plain_start = i = 0

    while i < len(text):
        # An escaped separator cannot open a quoted literal.
        if text.startswith(sep * 2, i):
            i += 2 * len(sep)
            continue

        if text.startswith(sep + "{", i):
            end = text.find(sep + "}", i + len(sep) + 1)
            if end != -1:
                parts.append(unicodedata.normalize("NFC", text[plain_start:i]))
                plain_start = end + len(sep) + 1
                parts.append(text[i:plain_start])
                i = plain_start
                continue

        i += 1

    parts.append(unicodedata.normalize("NFC", text[plain_start:]))
    return "".join(parts)
