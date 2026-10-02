from __future__ import annotations

import math
import statistics
from collections import defaultdict

from .fingerprint import simhash_similarity
from .models import FileRecord, SimilarityEdge


def similarity_score(left: FileRecord, right: FileRecord) -> tuple[float, str]:
    size_score = min(left.size, right.size) / max(left.size, right.size, 1)

    if left.is_text and right.is_text:
        assert left.simhash is not None and right.simhash is not None
        content = simhash_similarity(left.simhash, right.simhash)
        line_score = min(left.lines or 0, right.lines or 0) / max(left.lines or 1, right.lines or 1)
        extension = 1.0 if left.extension == right.extension else 0.0
        return (
            content * 0.68 + size_score * 0.14 + line_score * 0.10 + extension * 0.08,
            "text fingerprint",
        )

    extension = 1.0 if left.extension == right.extension else 0.0
    entropy_score = max(0.0, 1.0 - abs(left.entropy - right.entropy) / 8.0)
    printable_score = max(0.0, 1.0 - abs(left.printable_ratio - right.printable_ratio))
    return (
        size_score * 0.48 + extension * 0.24 + entropy_score * 0.18 + printable_score * 0.10,
        "binary structure",
    )


def analyze_records(
    records: list[FileRecord],
    *,
    similarity_threshold: float = 0.78,
) -> tuple[list[SimilarityEdge], list[list[str]], list[list[str]]]:
    hashes: dict[str, list[str]] = defaultdict(list)
    for record in records:
        hashes[record.sha256].append(record.path)

    duplicate_groups = sorted(
        [sorted(paths) for paths in hashes.values() if len(paths) > 1],
        key=lambda group: (-len(group), group[0]),
    )

    edges: list[SimilarityEdge] = []

    for i, left in enumerate(records):
        for right in records[i + 1:]:
            if left.sha256 == right.sha256:
                edges.append(SimilarityEdge(left.path, right.path, 1.0, "exact duplicate"))
                continue

            score, reason = similarity_score(left, right)
            if score >= similarity_threshold:
                edges.append(
                    SimilarityEdge(left.path, right.path, round(score, 4), reason)
                )

    edges.sort(key=lambda edge: (-edge.score, edge.left, edge.right))

    adjacency = {record.path: set() for record in records}
    for edge in edges:
        adjacency[edge.left].add(edge.right)
        adjacency[edge.right].add(edge.left)

    clusters: list[list[str]] = []
    visited: set[str] = set()

    for path in sorted(adjacency):
        if path in visited or not adjacency[path]:
            continue

        stack = [path]
        group: list[str] = []

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            group.append(current)
            stack.extend(adjacency[current] - visited)

        if len(group) > 1:
            clusters.append(sorted(group))

    clusters.sort(key=lambda group: (-len(group), group[0]))

    by_path = {record.path: record for record in records}
    for cluster_id, group in enumerate(clusters, start=1):
        for path in group:
            by_path[path].cluster = cluster_id

    _assign_anomalies(records)

    return edges, duplicate_groups, clusters


def _assign_anomalies(records: list[FileRecord]) -> None:
    if not records:
        return

    log_sizes = [math.log1p(record.size) for record in records]
    entropies = [record.entropy for record in records]
    size_center = statistics.median(log_sizes)
    entropy_center = statistics.median(entropies)
    size_mad = statistics.median(abs(value - size_center) for value in log_sizes)
    entropy_mad = statistics.median(abs(value - entropy_center) for value in entropies)

    extension_counts: dict[str, int] = defaultdict(int)
    for record in records:
        extension_counts[record.extension] += 1

    total = len(records)

    for record, log_size in zip(records, log_sizes):
        size_z = 0.0 if size_mad == 0 else 0.6745 * (log_size - size_center) / size_mad
        entropy_z = 0.0 if entropy_mad == 0 else 0.6745 * (record.entropy - entropy_center) / entropy_mad
        rarity = 1.0 - extension_counts[record.extension] / total

        record.anomaly_score = round(
            abs(size_z) * 0.55 + abs(entropy_z) * 0.30 + rarity * 1.30,
            3,
        )
