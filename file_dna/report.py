from __future__ import annotations

import html
import json
import math
from pathlib import Path

from .models import AnalysisReport, FileRecord


def write_json(report: AnalysisReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_html(report: AnalysisReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = report.to_dict()["summary"]
    positions = _layout(report.files)
    position_by_path = {record.path: pos for record, pos in positions}

    edge_svg: list[str] = []
    for edge in report.edges:
        left = position_by_path.get(edge.left)
        right = position_by_path.get(edge.right)
        if left is None or right is None:
            continue
        edge_svg.append(
            f'<line x1="{left[0]:.1f}" y1="{left[1]:.1f}" '
            f'x2="{right[0]:.1f}" y2="{right[1]:.1f}" '
            f'stroke="currentColor" stroke-opacity="{min(.5, .12 + edge.score * .25):.2f}" '
            f'stroke-width="{1 + edge.score * 1.4:.1f}"/>'
        )

    node_svg: list[str] = []
    for record, (x, y) in positions:
        radius = 5.5 + min(13.0, math.log2(record.size + 2) * 0.9)
        classes = ["node", "text" if record.is_text else "binary"]
        if record.anomaly_score >= 2.0:
            classes.append("anomaly")
        title = (
            f"{record.path} | {record.size} bytes | entropy {record.entropy:.2f} | "
            f"anomaly {record.anomaly_score:.2f}"
        )
        node_svg.append(
            f'<g class="{" ".join(classes)}"><circle cx="{x:.1f}" cy="{y:.1f}" '
            f'r="{radius:.1f}"><title>{html.escape(title)}</title></circle></g>'
        )

    duplicates = "".join(
        "<li>" + " ↔ ".join(html.escape(path) for path in group) + "</li>"
        for group in report.exact_duplicate_groups[:10]
    ) or "<li>No exact duplicates found.</li>"

    near = "".join(
        f"<li><strong>{edge.score * 100:.1f}%</strong> "
        f"{html.escape(edge.left)} ↔ {html.escape(edge.right)}</li>"
        for edge in [item for item in report.edges if item.score < 1.0][:10]
    ) or "<li>No near-duplicate pairs above threshold.</li>"

    anomalies = "".join(
        f"<tr><td>{html.escape(item.path)}</td><td>{item.anomaly_score:.2f}</td>"
        f"<td>{html.escape(item.extension)}</td><td>{_format_bytes(item.size)}</td></tr>"
        for item in sorted(report.files, key=lambda item: item.anomaly_score, reverse=True)[:8]
    )

    document = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>file-dna - {html.escape(Path(report.root).name)}</title>
<style>
*{{box-sizing:border-box}}:root{{font-family:Inter,system-ui,sans-serif;color:#17202a;background:#f4f6f8}}
body{{margin:0;padding:32px 18px}}main{{width:min(1180px,100%);margin:auto}}
.eyebrow{{font-size:10px;letter-spacing:.15em;font-weight:800;color:#778390}}
h1{{font-size:clamp(44px,7vw,76px);line-height:.92;letter-spacing:-.06em;margin:8px 0}}.muted{{color:#778390}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:28px 0}}
.card,.panel{{background:#fff;border-radius:20px;padding:18px}}
.card span{{display:block;color:#778390;font-size:10px;text-transform:uppercase;letter-spacing:.12em}}
.card strong{{display:block;font-size:27px;margin-top:4px}}
.map{{background:#0c1118;color:#9fb0c2;border-radius:26px;padding:14px;overflow:hidden}}
svg{{display:block;width:100%;height:auto}}.node circle{{fill:#5d97d8;stroke:#dce9f7;stroke-width:1}}
.node.binary circle{{fill:#9a78d0}}.node.anomaly circle{{stroke:#ffbc66;stroke-width:3}}
.columns{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}}
.panel h2{{margin:0 0 14px;font-size:21px;letter-spacing:-.03em}}
ul{{padding-left:18px;margin:0;color:#5f6c78;font-size:12px;line-height:1.7}}
table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #edf0f3}}
th{{color:#778390;font-size:10px;text-transform:uppercase;letter-spacing:.08em}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 0;color:#778390;font-size:11px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}
.legend .text{{background:#5d97d8}}.legend .binary{{background:#9a78d0}}.legend .anomaly{{background:#0c1118;border:2px solid #ffbc66}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}.columns{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<span class="eyebrow">FILE DNA REPORT</span>
<h1>{html.escape(Path(report.root).name)}</h1>
<p class="muted">Similarity, duplicates, clusters and anomalies derived locally from file metadata and fingerprints.</p>
<section class="grid">
<div class="card"><span>Files</span><strong>{summary["files"]}</strong></div>
<div class="card"><span>Duplicate groups</span><strong>{summary["exact_duplicate_groups"]}</strong></div>
<div class="card"><span>Similarity links</span><strong>{summary["similarity_edges"]}</strong></div>
<div class="card"><span>Clusters</span><strong>{summary["clusters"]}</strong></div>
</section>
<section class="map"><svg viewBox="0 0 1000 620" role="img" aria-label="File similarity map">
{''.join(edge_svg)}
{''.join(node_svg)}
</svg></section>
<div class="legend"><span><i class="text"></i>Text</span><span><i class="binary"></i>Binary</span><span><i class="anomaly"></i>Anomaly</span></div>
<section class="columns">
<div class="panel"><h2>Exact duplicates</h2><ul>{duplicates}</ul></div>
<div class="panel"><h2>Near duplicates</h2><ul>{near}</ul></div>
</section>
<section class="panel" style="margin-top:18px"><h2>Most unusual files</h2>
<table><thead><tr><th>File</th><th>Score</th><th>Type</th><th>Size</th></tr></thead>
<tbody>{anomalies}</tbody></table></section>
</main></body></html>'''

    output.write_text(document, encoding="utf-8")


def _layout(files: list[FileRecord]) -> list[tuple[FileRecord, tuple[float, float]]]:
    if not files:
        return []

    groups: dict[int, list[FileRecord]] = {}
    singleton = 10000

    for record in files:
        key = record.cluster
        if key is None:
            key = singleton
            singleton += 1
        groups.setdefault(key, []).append(record)

    items = list(groups.values())
    columns = max(1, math.ceil(math.sqrt(len(items))))
    rows = max(1, math.ceil(len(items) / columns))
    cell_w = 1000 / columns
    cell_h = 620 / rows
    result = []

    for index, group in enumerate(items):
        row, col = divmod(index, columns)
        cx = col * cell_w + cell_w / 2
        cy = row * cell_h + cell_h / 2

        if len(group) == 1:
            result.append((group[0], (cx, cy)))
            continue

        radius = min(cell_w, cell_h) * .28
        for item_index, record in enumerate(group):
            angle = 2 * math.pi * item_index / len(group)
            result.append((
                record,
                (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius),
            ))

    return result


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"
