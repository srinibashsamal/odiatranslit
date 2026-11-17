# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-17

First public release.

### Added

- `to_roman()` and `from_roman()` for converting Odia to Roman script and back.
- Three romanisation schemes: ISO 15919 (default), Hunterian and ITRANS.
- `transliterate()` to convert in either direction with one function
  (`reverse=True` for Roman → Odia).
- Scheme shortcuts: `to_iso15919()`, `from_iso15919()`, `to_hunterian()`,
  `from_hunterian()`, `to_itrans()` and `from_itrans()`.
- `reversible=True` option for an exact round-trip in ISO 15919 and ITRANS.
  Ambiguous letter pairs get a separator (`:` or `_`) and non-Odia text is
  quoted as `:{...:}` or `_{..._}`.
- Mixed-language text support: English words, numbers and punctuation pass
  through unchanged.
- Odia digit handling: kept in ISO 15919, converted to ASCII in Hunterian and
  in ITRANS (unless `reversible=True`).
- Common ITRANS alternative spellings such as `aa`, `ii`, `uu` and `R^i`.
- `odiatranslit` command-line tool with `--scheme`, `--reverse`,
  `--reversible`, `--input` and `--output` options.
- Type hints throughout, with a `py.typed` marker.
- Example scripts in `examples/` and a test suite in `tests/`.

### Notes

- Hunterian is lossy by design (for example ଣ, ଞ and ନ all become `n`), so
  converting it back to Odia is best-effort.
- The letter tables and transliteration engine are adapted from
  [OpenOdia](https://github.com/soumendrak/openodia) (MIT License).

[Unreleased]: https://github.com/srinibashsamal/odiatranslit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/srinibashsamal/odiatranslit/releases/tag/v0.1.0
