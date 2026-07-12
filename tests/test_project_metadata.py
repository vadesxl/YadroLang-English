import tomllib,unittest
from pathlib import Path
from src.version import VERSION
ROOT=Path(__file__).resolve().parents[1]
class ProjectMetadataTests(unittest.TestCase):
 def test_version_is_one_source_of_truth_across_main_page(self):
  project=tomllib.loads((ROOT/"pyproject.toml").read_text(encoding="utf-8"))["project"]
  readme=(ROOT/"README.md").read_text(encoding="utf-8")
  self.assertEqual("2.1.0",VERSION)
  self.assertEqual(VERSION,project["version"])
  self.assertEqual(f"# YadroLang (Kernel) {VERSION}",readme.splitlines()[0])
  self.assertIn(f"Code and package version: {VERSION}",readme)
 def test_main_page_does_not_resurrect_stale_release_claims(self):
  readme=(ROOT/"README.md").read_text(encoding="utf-8")
  for stale in ("What's New in v2.0","Features (v1.2)","v1.4.0 - Codegen hardening","~33 CI checks"):
   with self.subTest(stale=stale):self.assertNotIn(stale,readme)
 def test_security_boundaries_are_visible(self):
  readme=(ROOT/"README.md").read_text(encoding="utf-8")
  for boundary in ("Status: experimental","whole-program formal proof","not a complete memory-safe string model","not in this English facade","protection against every side channel"):
   with self.subTest(boundary=boundary):self.assertIn(boundary,readme)
if __name__=="__main__":unittest.main()
