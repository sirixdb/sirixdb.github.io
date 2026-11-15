"""Seed defects into a good site and verify that the validation gate kills them."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('check_site', Path(__file__).resolve().parents[1] / 'scripts/check_site.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class SiteMutationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.html = '<h1 id="top">Page</h1><h2 id="detail">Detail</h2><a href="#detail">Read</a><img src="image.svg" alt="Diagram">'
        (self.root / 'index.html').write_text(self.html)
        (self.root / 'image.svg').write_text('<svg/>')
        self.assertEqual([], checker.check_site(self.root)['errors'])

    def assert_mutation_killed(self, old, new, error):
        (self.root / 'index.html').write_text(self.html.replace(old, new))
        self.assertTrue(any(error in message for message in checker.check_site(self.root)['errors']))

    def test_missing_anchor(self):
        self.assert_mutation_killed('href="#detail"', 'href="#deleted"', 'missing anchor')

    def test_missing_image(self):
        self.assert_mutation_killed('src="image.svg"', 'src="missing.svg"', 'missing target')

    def test_duplicate_ids(self):
        self.assert_mutation_killed('id="detail"', 'id="top"', 'duplicate id')

    def test_missing_alt(self):
        self.assert_mutation_killed(' alt="Diagram"', '', 'image missing alt')

    def test_heading_gap(self):
        self.assert_mutation_killed('<h2 ', '<h4 ', 'heading skips')

    def test_multiple_page_titles(self):
        self.assert_mutation_killed('<h2 ', '<h1 ', 'expected one h1')

    def test_missing_srcset_image(self):
        self.assert_mutation_killed('src="image.svg"', 'src="image.svg" srcset="missing.svg 2x"', 'missing target')

    def test_relative_feed_url(self):
        (self.root / 'feed.xml').write_text('<rss><channel><link>/</link></channel></rss>')
        self.assertTrue(any('absolute HTTPS' in error for error in checker.check_site(self.root)['errors']))

    def test_missing_css_asset(self):
        (self.root / 'main.css').write_text('body { background: url(missing.png); }')
        self.assertTrue(any('missing target' in error for error in checker.check_site(self.root)['errors']))

    def test_same_site_absolute_anchor_is_checked(self):
        self.assert_mutation_killed('href="#detail"', 'href="https://sirix.io/#deleted"', 'missing anchor')

    def test_encoded_relative_path(self):
        (self.root / 'with space.html').write_text('<h1 id="yes">Target</h1>')
        (self.root / 'index.html').write_text(self.html + '<a href="with%20space.html#yes">Encoded</a>')
        self.assertEqual([], checker.check_site(self.root)['errors'])


if __name__ == '__main__':
    unittest.main()
