# file-dna

`file-dna` analyzes a directory and builds a compact "DNA profile" of its files.

It finds exact duplicates, near-duplicate text files, similarity clusters and unusual files, then exports the result as JSON or a standalone HTML map.

The project is dependency-free at runtime and uses only the Python standard library.

## File DNA

For each file the analyzer derives:

```text
SHA-256               exact identity
64-bit SimHash        approximate text similarity
file size             structural signal
extension             file family
byte entropy          content structure
printable ratio       text / binary signal
line count            text structure
average line length   text structure
```

## Features

- recursive folder scanning
- exact duplicate detection with SHA-256
- near-duplicate text detection with SimHash
- text and binary classification
- binary structural similarity
- file-size similarity
- byte entropy
- printable-byte ratio
- line and word statistics
- similarity graph
- connected similarity clusters
- robust anomaly score using median absolute deviation
- standalone HTML SVG map
- JSON export
- configurable similarity threshold
- configurable file-size limit
- no network requests
- zero runtime dependencies
- Python 3.11+

## Quick start

Run directly:

```bash
python -m file_dna.cli examples/sample \
  --json reports/sample.json \
  --html reports/sample.html
```

Or install as a CLI:

```bash
python -m pip install -e .
```

Then:

```bash
file-dna examples/sample \
  --json reports/sample.json \
  --html reports/sample.html
```

## Analyze another folder

```bash
file-dna ../my-project
```

With reports:

```bash
file-dna ../my-project \
  --json reports/file-dna.json \
  --html reports/file-dna.html
```

## Similarity model

Text similarity combines:

```text
68%  SimHash content similarity
14%  file-size similarity
10%  line-count similarity
 8%  extension match
```

The default threshold is `0.78`.

Use a stricter threshold:

```bash
file-dna . --threshold 0.86
```

Binary files are handled conservatively using size, extension, entropy and printable-byte ratio. Exact duplicates are always detected with SHA-256.

## Clusters

Similarity links form a graph. Connected components with at least two files become clusters.

If:

```text
A is similar to B
B is similar to C
```

the three files can belong to one cluster even when A and C are less similar directly.

## Anomalies

The anomaly score combines unusual:

- logarithmic file size
- byte entropy
- extension rarity

Median absolute deviation is used so a handful of huge files do not distort the baseline.

The score is a review signal, not a security verdict.

## HTML map

The generated standalone report shows:

```text
node size        file size
blue node        text file
purple node      binary file
orange outline   higher anomaly score
line             similarity relationship
local group      similarity cluster
```

No server is needed to open the report.

## Privacy

Everything runs locally.

Generated reports contain paths and derived metrics but do not contain full source-file contents.

## Ignored directories

By default:

```text
.git
.idea
.vscode
__pycache__
node_modules
.venv
venv
dist
build
coverage
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
file-dna/
├── file_dna/
│   ├── __init__.py
│   ├── analysis.py
│   ├── cli.py
│   ├── fingerprint.py
│   ├── models.py
│   ├── report.py
│   └── scanner.py
├── tests/
│   ├── test_analysis.py
│   └── test_fingerprint.py
├── examples/
│   └── sample/
├── pyproject.toml
├── LICENSE
└── README.md
```

## Future ideas

- perceptual image hashes
- MinHash for large document sets
- duplicate-directory detection
- `.gitignore` support
- cluster labels
- image thumbnails
- scan history in SQLite

## License

MIT
