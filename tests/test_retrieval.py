import unittest

from src.rag import build_index_from_corpus, retrieve


class RetrievalTests(unittest.TestCase):
    def test_retrieval_returns_similar_corpus_document(self):
        build_index_from_corpus()

        query = "Passport verification for Jane Smith"
        results = retrieve(query, k=2)

        self.assertTrue(results)
        self.assertIn("Jane Smith", results[0])
        self.assertIn("Passport", results[0])
        self.assertGreaterEqual(len(results), 1)

    def test_retrieval_handles_empty_query(self):
        build_index_from_corpus()

        query = ""
        results = retrieve(query, k=2)

        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
