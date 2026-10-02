from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def byte_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def printable_ratio(data: bytes) -> float:
    if not data:
        return 1.0
    printable = sum(
        1 for byte in data
        if byte in (9, 10, 13) or 32 <= byte <= 126
    )
    return printable / len(data)


def looks_like_text(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:8192]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return printable_ratio(sample) >= 0.82


def text_metrics(text: str) -> tuple[int, int, float]:
    lines = text.splitlines()
    words = TOKEN_RE.findall(text)
    line_count = max(1, len(lines))
    avg_line_length = sum(len(line) for line in lines) / line_count
    return line_count, len(words), avg_line_length


def simhash64(text: str) -> int:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    if not tokens:
        return 0

    features = tokens if len(tokens) < 3 else [
        " ".join(tokens[i:i + 3]) for i in range(len(tokens) - 2)
    ]

    vector = [0] * 64

    for feature in features:
        value = int.from_bytes(
            hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(),
            "big",
        )
        for bit in range(64):
            vector[bit] += 1 if value & (1 << bit) else -1

    result = 0
    for bit, weight in enumerate(vector):
        if weight >= 0:
            result |= 1 << bit
    return result


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def simhash_similarity(left: int, right: int) -> float:
    return 1.0 - hamming_distance(left, right) / 64.0


MINHASH_SIZE = 24
MINHASH_PRIME = (1 << 61) - 1


def _token_shingles(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]

    if not tokens:
        return []

    if len(tokens) < 3:
        return sorted(set(tokens))

    return sorted({
        " ".join(tokens[index:index + 3])
        for index in range(len(tokens) - 2)
    })


def minhash_signature(text: str, size: int = MINHASH_SIZE) -> list[int]:
    """Return a deterministic MinHash signature for token shingles.

    SimHash is good at measuring overall fingerprint distance. MinHash adds a
    separate estimate of token-set overlap, which helps distinguish files that
    merely have similar size/shape from files that actually share content.
    """
    shingles = _token_shingles(text)

    if not shingles:
        return [0] * size

    base_hashes = [
        int.from_bytes(
            hashlib.blake2b(
                shingle.encode("utf-8"),
                digest_size=8,
            ).digest(),
            "big",
        ) % MINHASH_PRIME
        for shingle in shingles
    ]

    signature: list[int] = []

    for index in range(size):
        # Deterministic coefficients for a family of universal hash functions.
        a = (1_103_515_245 + index * 2_654_435_761) % MINHASH_PRIME or 1
        b = (12_345 + index * 97_531) % MINHASH_PRIME

        signature.append(
            min((a * value + b) % MINHASH_PRIME for value in base_hashes)
        )

    return signature


def minhash_similarity(left: list[int], right: list[int]) -> float:
    if not left or not right:
        return 0.0

    length = min(len(left), len(right))

    if length == 0:
        return 0.0

    matches = sum(
        1 for index in range(length)
        if left[index] == right[index]
    )

    return matches / length
