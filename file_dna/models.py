from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FileRecord:
    path: str
    extension: str
    size: int
    sha256: str
    is_text: bool
    entropy: float
    printable_ratio: float
    lines: int | None = None
    words: int | None = None
    avg_line_length: float | None = None
    simhash: int | None = None
    minhash: list[int] | None = None
    anomaly_score: float = 0.0
    cluster: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.simhash is not None:
            data["simhash"] = f"{self.simhash:016x}"
        if self.minhash is not None:
            data["minhash"] = [f"{value:016x}" for value in self.minhash]
        return data


@dataclass(slots=True)
class SimilarityEdge:
    left: str
    right: str
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisReport:
    root: str
    files: list[FileRecord] = field(default_factory=list)
    edges: list[SimilarityEdge] = field(default_factory=list)
    exact_duplicate_groups: list[list[str]] = field(default_factory=list)
    clusters: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "summary": {
                "files": len(self.files),
                "bytes": sum(item.size for item in self.files),
                "text_files": sum(item.is_text for item in self.files),
                "binary_files": sum(not item.is_text for item in self.files),
                "exact_duplicate_groups": len(self.exact_duplicate_groups),
                "similarity_edges": len(self.edges),
                "clusters": len(self.clusters),
                "anomalies": sum(item.anomaly_score >= 2.0 for item in self.files),
            },
            "files": [item.to_dict() for item in self.files],
            "similarity_edges": [edge.to_dict() for edge in self.edges],
            "exact_duplicate_groups": self.exact_duplicate_groups,
            "clusters": self.clusters,
        }
