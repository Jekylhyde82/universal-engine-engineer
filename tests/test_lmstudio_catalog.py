import tempfile
import unittest
from pathlib import Path

from universal_engine.lmstudio_catalog import (
    LMStudioCatalogError, assimilate_public_catalog, discover_catalog,
)
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine


CATALOG_HTML = """
<html><body>
<a href="/models/lfm3"><h2>LFM3 2B</h2>
<span>Tool use Reasoning Vision</span>
<p>LFM3 is a vision-language model for on-device understanding.</p>
<span>Local — Available to download 4.8K downloads 18 stars Updated 23 days ago</span>
</a>
</body></html>
"""
DETAIL_HTML = """
<html><body>
<h1>LFM3</h1>
<p>LFM3-VL-2B is a vision-language model for on-device image and video understanding.</p>
<a href="https://huggingface.co/liquid-ai/lfm3-vl-2b">liquid/lfm3-vl-2b</a>
<h2>Memory Requirements</h2><p>To run the smallest LFM3, you need at least 1 GB of RAM.</p>
<h2>Capabilities</h2><p>LFM3 models support tool use, vision input, and reasoning. They are available in gguf.</p>
<h2>License</h2><p>LFM Open License v1.0</p>
</body></html>
"""


class CatalogTests(unittest.TestCase):
    def fetcher(self, url, timeout, max_bytes):
        if url == "https://lmstudio.ai/models":
            return CATALOG_HTML
        if url == "https://lmstudio.ai/models/lfm3":
            return DETAIL_HTML
        raise AssertionError(f"unexpected URL: {url}")

    def test_discovers_public_catalog_and_extracts_metadata(self):
        entries = discover_catalog(fetcher=self.fetcher)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.key, "lfm3")
        self.assertEqual(entry.display_name, "LFM3")
        self.assertIn("tool_use", entry.capability_tags)
        self.assertIn("vision", entry.capability_tags)
        self.assertIn("reasoning", entry.capability_tags)
        self.assertEqual(entry.minimum_memory, "1 GB")
        self.assertEqual(entry.max_context, None)
        self.assertEqual(entry.license_text, "LFM Open License v1.0")
        self.assertEqual(entry.download_count, "4.8K")
        self.assertTrue(any("huggingface.co" in item["url"] for item in entry.artifact_links))

    def test_rejects_non_lmstudio_catalog_origin(self):
        with self.assertRaises(LMStudioCatalogError):
            discover_catalog("https://example.com/models", fetcher=self.fetcher)

    def test_rejects_query_string_and_credentials(self):
        for url in ("https://lmstudio.ai/models?x=1", "https://user:pass@lmstudio.ai/models"):
            with self.subTest(url=url), self.assertRaises(LMStudioCatalogError):
                discover_catalog(url, fetcher=self.fetcher)

    def test_fails_closed_when_catalog_markup_has_no_model_links(self):
        with self.assertRaises(LMStudioCatalogError):
            discover_catalog(fetcher=lambda url, timeout, size: "<html><h1>Changed</h1></html>")

    def test_enforces_model_count_limit(self):
        with self.assertRaises(LMStudioCatalogError):
            discover_catalog(max_models=1, fetcher=lambda url, timeout, size:
                CATALOG_HTML.replace('href="/models/lfm3"', 'href="/models/lfm3"')
                + '<a href="/models/other">Other</a>')

    def test_assimilates_public_catalog_and_fuses_afi_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAcquisitionIntegrationEngine(Path(tmp) / "uaie.sqlite3")
            catalog_records, afi_records = assimilate_public_catalog(
                engine, fetcher=self.fetcher)
            self.assertEqual(len(catalog_records), 1)
            self.assertEqual(len(afi_records), 1)
            self.assertEqual(catalog_records[0].state, "assimilated")
            profile = engine.export_record(afi_records[0].record_id)
            self.assertEqual(profile["source"], "afi-prime://lm-studio-public-catalog/lfm3")
            self.assertIn("tool_use_listed_in_catalog", profile["extracted_text"])
            self.assertIn("PUBLISHER_REPORTED_CATALOG_METADATA", profile["extracted_text"])
            self.assertIn("METADATA_ONLY_NOT_BENCHMARKED", profile["extracted_text"])


if __name__ == "__main__":
    unittest.main()
