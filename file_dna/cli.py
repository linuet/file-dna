from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import analyze_records
from .models import AnalysisReport
from .report import write_html, write_json
from .scanner import scan_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-dna",
        description="Analyze duplicates, similarity clusters and anomalies in a directory.",
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--threshold", type=float, default=0.78)
    parser.add_argument("--max-file-mb", type=float, default=8.0)
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--json", dest="json_output")
    parser.add_argument("--html", dest="html_output")
    parser.add_argument("--top", type=int, default=10)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = Path(args.path)

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"file-dna: directory not found: {root}")
    if not 0 <= args.threshold <= 1:
        raise SystemExit("file-dna: --threshold must be between 0 and 1")
    if args.max_file_mb <= 0:
        raise SystemExit("file-dna: --max-file-mb must be positive")

    records = scan_directory(
        root,
        max_file_bytes=int(args.max_file_mb * 1024 * 1024),
        include_hidden=args.include_hidden,
    )
    edges, duplicate_groups, clusters = analyze_records(
        records,
        similarity_threshold=args.threshold,
    )

    report = AnalysisReport(
        root=str(root.resolve()),
        files=records,
        edges=edges,
        exact_duplicate_groups=duplicate_groups,
        clusters=clusters,
    )

    data = report.to_dict()
    summary = data["summary"]

    print("file-dna")
    print(report.root)
    print()
    print(f"files:              {summary['files']}")
    print(f"bytes:              {summary['bytes']}")
    print(f"text / binary:      {summary['text_files']} / {summary['binary_files']}")
    print(f"duplicate groups:   {summary['exact_duplicate_groups']}")
    print(f"similarity links:   {summary['similarity_edges']}")
    print(f"clusters:           {summary['clusters']}")
    print(f"high anomalies:     {summary['anomalies']}")

    anomalies = sorted(
        report.files,
        key=lambda item: item.anomaly_score,
        reverse=True,
    )[:max(0, args.top)]

    if anomalies:
        print("\nMost unusual files")
        for item in anomalies:
            print(f"{item.anomaly_score:6.2f}  {item.size:9d} B  {item.path}")

    if args.json_output:
        write_json(report, Path(args.json_output))
        print(f"\nJSON report: {args.json_output}")

    if args.html_output:
        write_html(report, Path(args.html_output))
        print(f"HTML report: {args.html_output}")


if __name__ == "__main__":
    main()
