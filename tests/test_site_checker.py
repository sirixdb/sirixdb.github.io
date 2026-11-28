"""Seed defects into a good site and verify that the validation gate kills them."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

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

    def test_relative_feed_urls(self):
        feed = ET.fromstring('<rss xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
                             '<link>https://sirix.io/</link>'
                             '<atom:link href="https://sirix.io/feed.xml" rel="self"/>'
                             '<item><link>https://sirix.io/post.html</link>'
                             '<guid>https://sirix.io/post.html</guid></item></channel></rss>')
        path = self.root / 'feed.xml'
        path.write_text(ET.tostring(feed, encoding='unicode'))
        self.assertEqual([], checker.check_site(self.root)['errors'])
        for selector, attribute, error in (
            ('.//channel/link', None, 'link/guid'),
            ('.//item/link', None, 'link/guid'),
            ('.//guid', None, 'link/guid'),
            ('.//{http://www.w3.org/2005/Atom}link', 'href', 'self link'),
        ):
            with self.subTest(selector=selector):
                element = feed.find(selector)
                original = element.get(attribute) if attribute else element.text
                if attribute:
                    element.set(attribute, '/')
                else:
                    element.text = '/'
                path.write_text(ET.tostring(feed, encoding='unicode'))
                self.assertEqual([f'feed.xml: {error} must be an absolute HTTPS URL'],
                                 checker.check_site(self.root)['errors'])
                if attribute:
                    element.set(attribute, original)
                else:
                    element.text = original

    def test_valid_empty_feed(self):
        # RSS permits an empty channel; removing template posts must not break it.
        feed = '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>' \
               '<title>SirixDB</title><description>Project updates</description>' \
               '<link>https://sirix.io/</link>' \
               '<atom:link href="https://sirix.io/feed.xml" rel="self" type="application/rss+xml"/>' \
               '</channel></rss>'
        (self.root / 'feed.xml').write_text(feed)
        self.assertEqual([], checker.check_site(self.root)['errors'])
        self.assertEqual([], ET.fromstring(feed).findall('.//item'))

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
