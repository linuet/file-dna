import unittest

from file_dna.analysis import analyze_records, similarity_score
from file_dna.models import FileRecord


def make_record(path, sha, simhash=0, minhash=None):
    return FileRecord(
        path=path,
        extension=".txt",
        size=100,
        sha256=sha,
        is_text=True,
        entropy=4.0,
        printable_ratio=1.0,
        lines=10,
        words=20,
        avg_line_length=10.0,
        simhash=simhash,
        minhash=minhash if minhash is not None else [1] * 24,
    )


class AnalysisTests(unittest.TestCase):
    def test_exact_duplicate_group(self):
        records = [
            make_record("a.txt", "same"),
            make_record("b.txt", "same"),
            make_record("c.txt", "other", (1 << 64) - 1),
        ]
        _, duplicates, _ = analyze_records(records)
        self.assertEqual(duplicates, [["a.txt", "b.txt"]])

    def test_matching_text_shape_scores_one(self):
        left = make_record("a.txt", "a", 123)
        right = make_record("b.txt", "b", 123)
        score, reason = similarity_score(left, right)
        self.assertEqual(reason, "simhash + minhash")
        self.assertAlmostEqual(score, 1.0)


    def test_minhash_can_reduce_false_positive(self):
        left = make_record("a.txt", "a", simhash=123, minhash=[1] * 24)
        right = make_record("b.txt", "b", simhash=123, minhash=[2] * 24)

        score, _ = similarity_score(left, right)

        self.assertLess(score, 0.80)



if __name__ == "__main__":
    unittest.main()
