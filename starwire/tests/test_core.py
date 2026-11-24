import json, tempfile, unittest
from pathlib import Path
from starwire.core import (Candidate, CandidateStore, CRAWLER_CAPABILITIES,
 IMPORTER_CAPABILITIES, SYPHON_CAPABILITIES, import_json, import_csv, import_xml,
 extract_html, extract_semantic_terms, validate_crawl_url, classify_format)

class StarwireTests(unittest.TestCase):
 def test_ninefold_registries(self):
  self.assertEqual(tuple(map(len,(CRAWLER_CAPABILITIES,IMPORTER_CAPABILITIES,SYPHON_CAPABILITIES))),(9,9,9))
 def test_json_import(self):
  got=import_json(json.dumps({"title":"GPU credits","summary":"Compute offer"}).encode(),"https://example.org/item")
  self.assertEqual(got[0].status,"discovered_unverified")
 def test_rejects_approval_claim(self):
  with self.assertRaises(ValueError):
   Candidate("x","https://example.org","json",status="approved").validated()
 def test_csv_import(self):
  got=import_csv(b"title,summary\nGrant,Research funding\n","https://example.org/feed")
  self.assertEqual(got[0].title,"Grant")
 def test_xml_import(self):
  got=import_xml(b"<rss><channel><item><title>Offer</title><description>Details</description></item></channel></rss>","https://example.org/rss")
  self.assertEqual(got[0].title,"Offer")
 def test_html_excludes_scripts(self):
  self.assertEqual(extract_html("<p>Useful</p><script>secret()</script>"),"Useful")
 def test_semantic_terms_deterministic(self):
  self.assertEqual(extract_semantic_terms("Cloud cloud GPU GPU hosting"),["cloud","gpu","hosting"])
 def test_allowlist_required(self):
  with self.assertRaises(ValueError): validate_crawl_url("https://example.org",set())
 def test_reject_private_ip(self):
  with self.assertRaises(ValueError): validate_crawl_url("https://127.0.0.1",{"127.0.0.1"})
 def test_store_deduplicates_without_losing_first_observation(self):
  with tempfile.TemporaryDirectory() as d:
   s=CandidateStore(str(Path(d)/"x.db"))
   c=Candidate("A","https://example.org/a","json","same")
   self.assertTrue(s.add(c)); self.assertFalse(s.add(c)); self.assertEqual(sum(s.report().values()),1); s.close()
 def test_format_classification(self):
  self.assertEqual(classify_format("feed.json"),"json")
if __name__=="__main__": unittest.main()
