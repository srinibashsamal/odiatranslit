"""Public transliteration API for Odia <-> Roman script.

Reversible mode (ISO15919 / ITRANS only)
----------------------------------------
When reversible=True:
- Adjacent tokens that would otherwise merge are separated with the
  scheme separator (':' or '_').
- Literal text that the decoder could misread is quoted as :{...:} or _{..._}.
- Literal separators are doubled (:: / __).
- Round-trip identity holds for the Odia runs after NFC normalisation.
Hunterian never supports reversible mode.
"""

from __future__ import annotations

from ._engine import (
    ITRANS_ALIASES,
    SEPARATORS,
    Scheme,
    _Decoder,
    _Encoder,
    _first_wins,
    _get_table,
    _join_tokens,
    _nfc_odia,
    _nfc_outside_quotes,
    _prepare,
    _quote_literals,
    _reverse_index,
)

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def to_roman(
    text: str,
    scheme: Scheme = "ISO15919",
    *,
    reversible: bool = False,
) -> str:
    """Transliterate Odia text into Roman script.

    Supports mixed-language text: non-Odia characters (ASCII, punctuation,
    whitespace, or other scripts) are passed through unchanged unless escaped
    by ``reversible=True``. Adjacent Odia tokens that would merge into a
    longer spelling are disambiguated with a scheme separator (``:`` in
    ISO15919, ``_`` in ITRANS), such as ``କଇ`` -> ``"ka:i"`` or ``କ୍ଅ`` ->
    ``"k:a"``.

    Args:
        text (str): Odia or mixed-language text to transliterate.
        scheme (Scheme, optional): Romanisation scheme to use:
            ``"ISO15919"`` (academic diacritics, reversible),
            ``"Hunterian"`` (plain ASCII, lossy), or ``"ITRANS"``
            (case-sensitive ASCII, reversible). Defaults to ``"ISO15919"``.
        reversible (bool, optional): ISO15919 and ITRANS only. Escapes any
            literal text or stray signs that ``from_roman`` could misread, so
            that ``from_roman(to_roman(s, scheme, reversible=True), scheme) == s``
            (when Odia runs are compared in NFC). Literal separators are
            doubled (``::`` / ``__``) and ambiguous non-Odia runs are wrapped
            as ``:{...:}`` / ``_{..._}``. Ignored for Hunterian. Defaults to
            ``False``.

    Returns:
        str: Transliterated text in the requested Roman scheme.

    Notes:
        - Odia digits (``୦``–``୯``) become ASCII digits in Hunterian, and in
          ITRANS unless ``reversible=True``. ISO15919 keeps them as Odia
          digits.
        - ``ଡ଼`` and ``ଢ଼`` use their dedicated spellings (``ṛ``/``ṛh``,
          ``.D``/``.Dh``, or ``r``/``rh``). A nukta (``଼``) on any other
          character is written as ``"·"`` (ISO15919) or ``"`"`` (ITRANS),
          and dropped in Hunterian.

    Raises:
        ValueError: If ``scheme`` is not supported.

    Examples:
        >>> to_roman("ଓଡ଼ିଆ")
        'ōṛiā'
        >>> to_roman("ନମସ୍କାର", "Hunterian")
        'namaskara'
        >>> to_roman("କଇ", "ISO15919", reversible=True)
        'ka:i'
        >>> to_roman("Hello ଓଡ଼ିଆ!", "ISO15919", reversible=True)
        ':{Hello:} ōṛiā!'
    """
    table = _get_table(scheme)
    sep = SEPARATORS.get(scheme)
    escape = reversible and sep is not None

    encoder = _Encoder(table, scheme, sep, escape)
    for ch in _prepare(text, scheme, reversible):
        encoder.feed(ch)

    encoder.flush_schwa()

    tokens = encoder.out
    literal = encoder.literal

    if escape:
        tokens, literal = _quote_literals(tokens, literal, scheme)

    return _join_tokens(tokens, scheme, literal)


def from_roman(text: str, scheme: Scheme = "ISO15919") -> str:
    """Transliterate Roman text back into Odia (inverse of ``to_roman``).

    Reads Romanised text left-to-right using longest-match tokenisation and
    passes unrecognised characters (including mixed-language text) through
    unchanged. A vowel immediately after a consonant becomes a dependent vowel
    sign (matra); the inherent ``"a"`` adds no sign; a consonant with no
    following vowel receives a halant (``୍``).

    Scheme-specific features:
        - **ISO15919**: Normalises decomposed Unicode diacritics outside quoted
          literals (so e.g. ``"a\\u0304"`` matches ``"ā"``) and recognises
          ``:`` boundaries, ``::`` literal colons, and ``:{...:}`` quotes.
        - **ITRANS**: Also accepts common alternative ASCII spellings
          (``aa``, ``ii``, ``uu``, ``R^i``, ``R^I``, ``L^i``, ``L^I``) and
          recognises ``_`` boundaries, ``__`` literal underscores, and
          ``_{..._}`` quotes.
        - **Hunterian**: Best-effort decoding only. Prefers common Odia
          letters for shared spellings (``ନ``, ``ତ``, ``ଥ``, ``ଦ``, ``ଧ``)
          and reads ``"ri"``/``"li"`` as consonant + vowel (e.g. ``"kri"`` ->
          ``"କ୍ରି"``). Because ``ଂ``, ``ଁ``, and ``ଃ`` have no distinct
          Hunterian spelling, a lone ``"n"`` or ``"h"`` is decoded as ``ନ``
          or ``ହ``, and ``"'"`` is decoded as the avagraha ``ଽ``.

    Args:
        text (str): Romanised Odia or mixed-language text to convert.
        scheme (Scheme, optional): Romanisation scheme used in ``text``.
            One of ``"ISO15919"``, ``"Hunterian"``, or ``"ITRANS"``. Defaults
            to ``"ISO15919"``.

    Returns:
        str: Decoded Odia text (with Odia script runs normalised to NFC).

    Raises:
        ValueError: If ``scheme`` is not supported.

    Examples:
        >>> from_roman("namaskāra")
        'ନମସ୍କାର'
        >>> from_roman("ā")
        'ଆ'
        >>> from_roman("ka:i")
        'କଇ'
        >>> from_roman("namaskAra", "ITRANS")
        'ନମସ୍କାର'
        >>> from_roman("jesan", "Hunterian")
        'ଜେସନ୍'
    """
    rev = _reverse_index(scheme)
    table = _get_table(scheme)

    matras = _first_wins(table["matras"].items())
    if scheme == "ITRANS":
        for alias, canonical in ITRANS_ALIASES.items():
            matras[alias] = matras[canonical]

    sep = SEPARATORS.get(scheme)
    if scheme == "ISO15919" and sep is not None:
        text = _nfc_outside_quotes(text, sep)

    decoder = _Decoder(
        text,
        rev.by_first,
        rev.entries,
        matras,
        table["schwa"],
        sep,
    )

    while decoder.i < len(text):
        decoder.step()

    decoder.close_consonant()

    return _nfc_odia("".join(decoder.out))


def transliterate(
    text: str,
    scheme: Scheme = "ISO15919",
    *,
    reverse: bool = False,
    reversible: bool = False,
) -> str:
    """Transliterate between Odia and Roman script in either direction.

    Single-entry wrapper dispatching to ``to_roman`` (when ``reverse=False``)
    or ``from_roman`` (when ``reverse=True``), mirroring the CLI options.

    Args:
        text (str): Input text (Odia when ``reverse=False``, Roman when
            ``reverse=True``). Mixed-language text is supported.
        scheme (Scheme, optional): Romanisation scheme (``"ISO15919"``,
            ``"Hunterian"``, or ``"ITRANS"``). Defaults to ``"ISO15919"``.
        reverse (bool, optional): If ``True``, convert Roman -> Odia instead
            of Odia -> Roman. Defaults to ``False``.
        reversible (bool, optional): Only valid when ``reverse=False``.
            Escapes output for exact round-tripping in ISO15919 or ITRANS.
            Ignored for Hunterian. Defaults to ``False``.

    Returns:
        str: Transliterated text in the target script.

    Raises:
        ValueError: If ``scheme`` is unknown, or if both ``reverse=True``
            and ``reversible=True`` are given.

    Examples:
        >>> transliterate("ଓଡ଼ିଆ")
        'ōṛiā'
        >>> transliterate("namaskAra", "ITRANS", reverse=True)
        'ନମସ୍କାର'
    """
    if reverse and reversible:
        raise ValueError("reversible=True only applies when reverse=False")
    if reverse:
        return from_roman(text, scheme)
    return to_roman(text, scheme, reversible=reversible)


# ---------------------------------------------------------------------------
# Scheme-specific shortcuts
# ---------------------------------------------------------------------------


def to_iso15919(text: str, *, reversible: bool = False) -> str:
    """Transliterate Odia text to ISO 15919 Roman script.

    Shortcut for ``to_roman(text, "ISO15919", reversible=reversible)``.

    Examples:
        >>> to_iso15919("ଓଡ଼ିଆ")
        'ōṛiā'
        >>> to_iso15919("କଇ", reversible=True)
        'ka:i'
    """
    return to_roman(text, "ISO15919", reversible=reversible)


def from_iso15919(text: str) -> str:
    """Transliterate ISO 15919 Roman text back into Odia.

    Shortcut for ``from_roman(text, "ISO15919")``.

    Examples:
        >>> from_iso15919("namaskāra")
        'ନମସ୍କାର'
        >>> from_iso15919("ka:i")
        'କଇ'
    """
    return from_roman(text, "ISO15919")


def to_hunterian(text: str) -> str:
    """Transliterate Odia text to plain ASCII using the Hunterian scheme.

    Shortcut for ``to_roman(text, "Hunterian")``. Hunterian is lossy by
    design, so there is no ``reversible`` option.

    Examples:
        >>> to_hunterian("ନମସ୍କାର")
        'namaskara'
    """
    return to_roman(text, "Hunterian")


def from_hunterian(text: str) -> str:
    """Transliterate Hunterian ASCII text into Odia (best-effort).

    Shortcut for ``from_roman(text, "Hunterian")``. Shared spellings decode
    to the more common Odia letter (``ନ``, ``ତ``, ``ଥ``, ``ଦ``, ``ଧ``).

    Examples:
        >>> from_hunterian("jesan")
        'ଜେସନ୍'
    """
    return from_roman(text, "Hunterian")


def to_itrans(text: str, *, reversible: bool = False) -> str:
    """Transliterate Odia text to ASCII using the ITRANS scheme.

    Shortcut for ``to_roman(text, "ITRANS", reversible=reversible)``.

    Examples:
        >>> to_itrans("ନମସ୍କାର")
        'namaskAra'
        >>> to_itrans("କଅ", reversible=True)
        'ka_a'
    """
    return to_roman(text, "ITRANS", reversible=reversible)


def from_itrans(text: str) -> str:
    """Transliterate ITRANS ASCII text back into Odia.

    Shortcut for ``from_roman(text, "ITRANS")``. Also accepts alternative
    spellings such as ``aa``, ``ii``, ``uu`` and ``R^i``.

    Examples:
        >>> from_itrans("namaskAra")
        'ନମସ୍କାର'
    """
    return from_roman(text, "ITRANS")
