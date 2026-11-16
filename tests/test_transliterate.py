"""Tests for odiatranslit."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import odiatranslit as ot
from odiatranslit import (
    SCHEMES,
    __version__,
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
from odiatranslit.cli import main

# ---------------------------------------------------------------------------
# Odia -> Roman
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("odia", "scheme", "expected"),
    [
        ("ଓଡ଼ିଆ", "ISO15919", "ōṛiā"),
        ("ଓଡ଼ିଆ ଭାଷା", "ISO15919", "ōṛiā bhāṣā"),
        ("ଓଡ଼ିଆ ଭାଷା", "Hunterian", "oria bhasha"),
        ("ଓଡ଼ିଆ ଭାଷା", "ITRANS", "o.DiA bhAShA"),
        ("ନମସ୍କାର", "ISO15919", "namaskāra"),
        ("ନମସ୍କାର", "Hunterian", "namaskara"),
        ("ନମସ୍କାର", "ITRANS", "namaskAra"),
        ("ଜଗନ୍ନାଥ", "Hunterian", "jagannatha"),
    ],
)
def test_to_roman(odia: str, scheme: str, expected: str) -> None:
    assert to_roman(odia, scheme) == expected  # type: ignore[arg-type]


def test_to_roman_default_scheme_is_iso() -> None:
    assert to_roman("ଓଡ଼ିଆ") == to_roman("ଓଡ଼ିଆ", "ISO15919")


def test_non_odia_text_passes_through() -> None:
    assert to_roman("Hello, 123!") == "Hello, 123!"


def test_empty_string() -> None:
    for scheme in SCHEMES:
        assert to_roman("", scheme) == ""
        assert from_roman("", scheme) == ""


def test_separator_added_between_merging_tokens() -> None:
    # କଇ must not be written as "kai", which would read back as କୈ.
    assert to_roman("କଇ", "ISO15919") == "ka:i"
    assert from_roman("ka:i", "ISO15919") == "କଇ"


# ---------------------------------------------------------------------------
# Digits
# ---------------------------------------------------------------------------


def test_odia_digits() -> None:
    assert to_roman("୧୨୩", "Hunterian") == "123"
    assert to_roman("୧୨୩", "ITRANS") == "123"
    assert to_roman("୧୨୩", "ISO15919") == "୧୨୩"
    assert to_roman("୧୨୩", "ITRANS", reversible=True) == "୧୨୩"


# ---------------------------------------------------------------------------
# Roman -> Odia
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("roman", "scheme", "expected"),
    [
        ("namaskāra", "ISO15919", "ନମସ୍କାର"),
        ("ā", "ISO15919", "ଆ"),
        ("namaskAra", "ITRANS", "ନମସ୍କାର"),
        ("jesan", "Hunterian", "ଜେସନ୍"),
        ("kri", "Hunterian", "କ୍ରି"),
    ],
)
def test_from_roman(roman: str, scheme: str, expected: str) -> None:
    assert from_roman(roman, scheme) == expected  # type: ignore[arg-type]


def test_itrans_aliases() -> None:
    assert from_roman("namaskaara", "ITRANS") == from_roman("namaskAra", "ITRANS")


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
@pytest.mark.parametrize(
    "text",
    [
        "ଓଡ଼ିଆ ଭାଷା",
        "ଜଗନ୍ନାଥ Puri",
        "ନମସ୍କାର",
        "କଇ",
        "କ୍ହ",
        "କ୍୍ଅ",
        "a:b_c",
        "୧୨୩ ଟଙ୍କା",
        "Hello ଓଡ଼ିଆ world!",
    ],
)
def test_roundtrip(text: str, scheme: str) -> None:
    roman = to_roman(text, scheme, reversible=True)  # type: ignore[arg-type]
    assert from_roman(roman, scheme) == text  # type: ignore[arg-type]


def test_itrans_reversible_quotes_english() -> None:
    assert to_roman("ଜଗନ୍ନାଥ Puri", "ITRANS", reversible=True) == "jagannAtha _{Puri_}"


# ---------------------------------------------------------------------------
# Shortcuts and transliterate()
# ---------------------------------------------------------------------------


def test_scheme_shortcuts_match_core_functions() -> None:
    text = "ଓଡ଼ିଆ ଭାଷା"
    assert to_iso15919(text) == to_roman(text, "ISO15919")
    assert to_hunterian(text) == to_roman(text, "Hunterian")
    assert to_itrans(text) == to_roman(text, "ITRANS")
    assert to_itrans(text, reversible=True) == to_roman(text, "ITRANS", reversible=True)

    assert from_iso15919("namaskāra") == from_roman("namaskāra", "ISO15919")
    assert from_hunterian("jesan") == from_roman("jesan", "Hunterian")
    assert from_itrans("namaskAra") == from_roman("namaskAra", "ITRANS")


def test_transliterate_both_directions() -> None:
    assert transliterate("ଓଡ଼ିଆ") == "ōṛiā"
    assert transliterate("namaskAra", "ITRANS", reverse=True) == "ନମସ୍କାର"


def test_transliterate_rejects_reverse_with_reversible() -> None:
    with pytest.raises(ValueError, match="reversible"):
        transliterate("a", reverse=True, reversible=True)


# ---------------------------------------------------------------------------
# Package structure
# ---------------------------------------------------------------------------


def test_function_does_not_shadow_engine_module() -> None:
    engine = importlib.import_module("odiatranslit._engine")
    assert callable(ot.transliterate)
    assert hasattr(engine, "_Encoder")


def test_all_exports_exist() -> None:
    for name in ot.__all__:
        assert hasattr(ot, name), name


def test_version() -> None:
    assert isinstance(__version__, str)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def test_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="unknown scheme"):
        to_roman("ଓଡ଼ିଆ", "IAST")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown scheme"):
        from_roman("odia", "IAST")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_to_roman(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ଓଡ଼ିଆ"]) == 0
    assert capsys.readouterr().out == "ōṛiā\n"


def test_cli_reverse(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["-r", "namaskAra", "-s", "ITRANS"]) == 0
    assert capsys.readouterr().out == "ନମସ୍କାର\n"


def test_cli_files(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    dst = tmp_path / "out.txt"
    src.write_text("ଓଡ଼ିଆ\n", encoding="utf-8")
    assert main(["-i", str(src), "-o", str(dst), "-s", "Hunterian"]) == 0
    assert dst.read_text(encoding="utf-8") == "oria\n"


def test_cli_rejects_reverse_with_reversible() -> None:
    with pytest.raises(SystemExit):
        main(["-r", "--reversible", "a"])
