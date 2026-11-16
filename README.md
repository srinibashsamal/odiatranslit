# Odia Transliterate

Convert Odia text to Roman (Latin) script and back, in pure Python.

Supports three romanisation schemes, works in both directions, and can
round-trip text without any loss.

```python
>>> from odia_transliterate import to_roman, from_roman
>>> to_roman("ଓଡ଼ିଆ ଭାଷା")
'ōṛiā bhāṣā'
>>> from_roman("namaskAra", "ITRANS")
'ନମସ୍କାର'

```

## Features

- **Two directions**: Odia → Roman with `to_roman`, Roman → Odia with `from_roman`
- **Three schemes**: ISO 15919, Hunterian and ITRANS
- **Lossless round-trip** for ISO 15919 and ITRANS with `reversible=True`
- **Mixed text is safe**: English words, numbers and punctuation pass through untouched
- **Command-line tool** included
- **No dependencies**, fully type-hinted

## Installation

```bash
pip install odia-transliterate
```

Requires Python 3.9 or later.

## Schemes

| Scheme               | Best for                                | Example: ଓଡ଼ିଆ ଭାଷା | Reversible |
| -------------------- | --------------------------------------- | ------------------- | ---------- |
| `ISO15919` (default) | Academic writing, citations, catalogues | `ōṛiā bhāṣā`        | Yes        |
| `ITRANS`             | Typing Odia on an English keyboard      | `o.DiA bhAShA`      | Yes        |
| `Hunterian`          | Names, places, URLs, search             | `oria bhasha`       | No (lossy) |

## Usage

### Odia → Roman

```python
from odia_transliterate import to_roman

to_roman("ଓଡ଼ିଆ")  # 'ōṛiā'
to_roman("ନମସ୍କାର", "Hunterian")  # 'namaskara'
to_roman("ନମସ୍କାର", "ITRANS")  # 'namaskAra'
```

### Roman → Odia

```python
from odia_transliterate import from_roman

from_roman("namaskāra")  # 'ନମସ୍କାର'
from_roman("namaskAra", "ITRANS")  # 'ନମସ୍କାର'
from_roman("jesan", "Hunterian")  # 'ଜେସନ୍'
```

### One function for both directions

```python
from odia_transliterate import transliterate

transliterate("ଓଡ଼ିଆ")  # 'ōṛiā'
transliterate("namaskAra", "ITRANS", reverse=True)  # 'ନମସ୍କାର'
```

### Scheme shortcuts

| Odia → Roman                          | Roman → Odia           |
| ------------------------------------- | ---------------------- |
| `to_iso15919(text, reversible=False)` | `from_iso15919(text)`  |
| `to_itrans(text, reversible=False)`   | `from_itrans(text)`    |
| `to_hunterian(text)`                  | `from_hunterian(text)` |

```python
from odia_transliterate import to_itrans, from_itrans

to_itrans("ନମସ୍କାର")  # 'namaskAra'
from_itrans("namaskAra")  # 'ନମସ୍କାର'
```

### Lossless round-trip

Pass `reversible=True` when you need to get the exact original text back.
Anything that could be misread is escaped.

```python
text = "ଜଗନ୍ନାଥ Puri"

roman = to_roman(text, "ITRANS", reversible=True)  # 'jagannAtha _{Puri_}'
assert from_roman(roman, "ITRANS") == text
```

`reversible` works with ISO 15919 and ITRANS. Hunterian merges several
letters (for example ଣ, ଞ and ନ all become `n`), so it cannot be reversed
exactly.

### With pandas

```python
df["name_roman"] = df["name_odia"].map(to_hunterian)
```

## Command line

```bash
odia-transliterate "ଓଡ଼ିଆ"                     # ōṛiā
odia-transliterate "ନମସ୍କାର" -s Hunterian       # namaskara
odia-transliterate -r "namaskAra" -s ITRANS    # ନମସ୍କାର
odia-transliterate -i input.txt -o output.txt
echo "ଜଗନ୍ନାଥ" | odia-transliterate
```

| Option            | Description                                           |
| ----------------- | ----------------------------------------------------- |
| `text`            | Text to convert (reads from `-i` or stdin if omitted) |
| `-s`, `--scheme`  | `ISO15919` (default), `Hunterian` or `ITRANS`         |
| `-r`, `--reverse` | Convert Roman → Odia                                  |
| `--reversible`    | Escape output so it converts back exactly             |
| `-i`, `--input`   | Read from a UTF-8 file                                |
| `-o`, `--output`  | Write to a file instead of the screen                 |

## Notes

- Odia digits (୦–୯) become ASCII digits in Hunterian, and in ITRANS
  unless `reversible=True`. ISO 15919 keeps them as they are.
- ଡ଼ and ଢ଼ have their own spellings: `ṛ`/`ṛh` (ISO), `.D`/`.Dh` (ITRANS),
  `r`/`rh` (Hunterian).
- ITRANS also accepts common alternatives such as `aa` for `A` and `ii` for `I`.
- Hunterian decoding is best-effort. Where a spelling is shared, the most
  common Odia letter is chosen.

## Development

```bash
pip install -e ".[dev]"
pytest              # unit tests + docstring examples
ruff check .
mypy
```

## Project layout

```
odia-transliterate/
├── odia_transliterate/
│   ├── __init__.py        # public exports
│   ├── api.py             # public functions
│   ├── _engine.py         # internal encoder / decoder
│   ├── schemes.py         # letter tables for each scheme
│   ├── cli.py             # command-line tool
│   └── py.typed
├── tests/
│   └── test_transliterate.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## Acknowledgements

The letter tables and transliteration engine are adapted from
[OpenOdia](https://github.com/soumendrak/openodia) (MIT License).

## Contributing

Bug reports and suggestions are welcome. Please
[open an issue](https://github.com/srinibashsamal/odia-transliterate/issues)
with the input text, the scheme used, and the output you expected.

## License

MIT. See [LICENSE](LICENSE).
