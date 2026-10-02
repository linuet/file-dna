import unittest

from file_dna.fingerprint import (
    byte_entropy,
    hamming_distance,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
)


class FingerprintTests(unittest.TestCase):
    def test_identical_text_has_identical_simhash(self):
        left = simhash64("alpha beta gamma delta")
        right = simhash64("alpha beta gamma delta")
        self.assertEqual(left, right)
        self.assertEqual(simhash_similarity(left, right), 1.0)

    def test_similar_text_beats_unrelated_text(self):
        base = simhash64("server request latency retry timeout response")
        similar = simhash64("server request latency retry timeout response cache")
        unrelated = simhash64("banana orange garden music mountain telescope")
        self.assertGreater(
            simhash_similarity(base, similar),
            simhash_similarity(base, unrelated),
        )


    def test_minhash_separates_similar_and_unrelated_text(self):
        base = minhash_signature(
            "server request latency retry timeout response cache"
        )
        similar = minhash_signature(
            "server request latency retry timeout response cache database"
        )
        unrelated = minhash_signature(
            "banana garden telescope mountain piano ocean"
        )

        self.assertGreater(
            minhash_similarity(base, similar),
            minhash_similarity(base, unrelated),
        )

    def test_hamming_distance(self):
        self.assertEqual(hamming_distance(0b1010, 0b1110), 1)

    def test_entropy_empty(self):
        self.assertEqual(byte_entropy(b""), 0.0)


if __name__ == "__main__":
    unittest.main()
