# Lakṣmīnārāyaṇa Saṃhitā Corpus

A reproducible, verse-addressable digital research corpus of the **Lakṣmīnārāyaṇa Saṃhitā (LNS)**, derived primarily from the Sanskrit Wikisource transcription.

The project preserves an immutable revision-pinned source snapshot and generates normalized research views without silently changing the Sanskrit source text.

## Corpus structure

The source tree represents all **1,250 chapter pages** of the four santānas/khaṇḍas:

| Khaṇḍa | Santāna | Chapters |
|---|---|---:|
| 1 | Kṛtayuga-santāna | 590 |
| 2 | Tretāyuga-santāna | 300 |
| 3 | Dvāparayuga-santāna | 237 |
| 4 | Tiṣya-santāna | 123 |

The editorial source declares **125,988 ślokas** in total. That number is retained as an editorial checksum, not forced as a segmentation target. The corpus records only verse boundaries that can be supported by the digital witness or by explicitly documented source repairs.

### Known source gap

**LNS 2.96** has a Sanskrit Wikisource page but no Sanskrit chapter text in the audited source snapshot. No verses are invented or silently reconstructed. See [`docs/SOURCE_GAPS.md`](docs/SOURCE_GAPS.md).

## Human-readable access

Each successful GitHub Actions build generates:

- `consolidated/LNS-devanagari.txt` — GRETIL-style consolidated plain text
- `consolidated/LNS-iast.txt` — consolidated IAST
- `consolidated/LNS-slp1.txt` — consolidated SLP1
- `consolidated/LNS-devanagari.html` — full Devanāgarī HTML with stable verse anchors
- `consolidated/LNS-iast.html` — full IAST HTML with stable verse anchors
- `site/` — navigable static site with 1,250 chapter pages plus the two consolidated HTML views

Canonical verse identifiers use the form:

```text
LNS_3.173.52
```

In HTML the same identifier is a fragment anchor:

```text
#LNS_3.173.52
```

This allows direct linking to individual verses while retaining full-browser `Ctrl/Cmd+F` searching comparable to a GRETIL text page.

## Web publication

The build workflow publishes the generated `site/` directory to the `gh-pages` branch. Once GitHub Pages is configured to serve that branch, the corpus becomes directly browsable as a static website.

## Machine-readable research layers

The build also produces:

- `metadata/verses.csv` — verse ID, Devanāgarī, IAST, SLP1, source revision and marker metadata
- `metadata/chapters.csv` — chapter-level source and segmentation metadata
- `reports/anomalies.json` — all parsing/source anomalies and explicit repairs
- `reports/validation.json` — structural validation and source-gap status
- per-chapter Devanāgarī, IAST and SLP1 text files

## Source integrity policy

The project follows four rules:

1. **Never silently correct the Sanskrit source.**
2. **Preserve the revision-pinned Wikisource snapshot unchanged.**
3. **Record structural repairs explicitly and reproducibly.**
4. **Distinguish source gaps, printed-number anomalies and segmentation errors.**

Snapshot-specific repairs live in `lns_corpus/source_repairs.py`. They are exact-string keyed so that a future correction in Wikisource causes the old repair to stop matching automatically.

## Rebuild

The GitHub Actions workflow downloads the current revision-pinned Wikisource pages, constructs the corpus, validates it, generates Devanāgarī/IAST/SLP1 outputs, builds the HTML interface, uploads reproducible artifacts, and publishes the generated site branch.

The same pipeline can be run locally with Python 3.12 after installing the project dependencies.

## Attribution and licensing

See [`ATTRIBUTION.md`](ATTRIBUTION.md) and the repository license files. The textual corpus is derived from Sanskrit Wikisource and must retain the applicable Wikimedia/Wikisource attribution and share-alike requirements. Pipeline code is licensed separately as indicated in `LICENSE-CODE`.
