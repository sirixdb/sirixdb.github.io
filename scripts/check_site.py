#!/usr/bin/env python3
"""Check a built Jekyll site without third-party dependencies.

External checks are optional: network errors, rate limits and bot challenges are
reported as unresolved, never silently counted as passing links.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids = set()
        self.links = []
        self.errors = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identity = attrs.get('id') or (attrs.get('name') if tag == 'a' else None)
        if identity:
            if identity in self.ids:
                self.errors.append(f'{self.source}: duplicate id {identity}')
            self.ids.add(identity)
        if tag == 'img' and 'alt' not in attrs:
            self.errors.append(f'{self.source}: image missing alt')
        if re.fullmatch(r'h[1-6]', tag):
            level = int(tag[1])
            if self.headings and level > self.headings[-1] + 1:
                self.errors.append(f'{self.source}: heading skips h{self.headings[-1]} to {tag}')
            self.headings.append(level)
        if tag == 'link' and set(attrs.get('rel', '').split()) & {'preconnect', 'dns-prefetch'}:
            return
        for key in ('href', 'src', 'poster'):
            if attrs.get(key):
                self.links.append(attrs[key])
        if attrs.get('srcset') and not attrs['srcset'].startswith('data:'):
            self.links.extend(item.strip().split()[0] for item in attrs['srcset'].split(',') if item.strip())


def check_site(root):
    root = Path(root).resolve()
    pages = {}
    errors = []
    external = set()
    for path in sorted(root.rglob('*.html')):
        key = path.relative_to(root).as_posix()
        page = Page(key)
        page.feed(path.read_text(encoding='utf-8'))
        pages[key] = page
        errors.extend(page.errors)
        if page.headings.count(1) != 1:
            errors.append(f'{key}: expected one h1, found {page.headings.count(1)}')
    references = [(name, link) for name, page in pages.items() for link in page.links]
    for path in root.rglob('*.css'):
        references.extend((path.relative_to(root).as_posix(), ref) for ref in
                          re.findall(r'url\([\s\'"]*([^\s)\'"]+)', path.read_text(encoding='utf-8')))
    for source, ref in references:
        parsed = urlsplit(ref)
        if parsed.scheme in ('mailto', 'tel', 'data', 'javascript'):
            continue
        if parsed.netloc and parsed.hostname not in ('sirix.io', 'www.sirix.io'):
            if parsed.scheme in ('http', 'https', ''):
                external.add(urldefrag(ref if parsed.scheme else 'https:' + ref)[0])
            continue
        target = urlsplit(urljoin('https://sirix.io/' + source, ref))
        relative = unquote(target.path).lstrip('/')
        path = root / relative
        if path.is_dir():
            path = path / 'index.html'
        if not path.is_file():
            errors.append(f'{source}: missing target {ref}')
            continue
        fragment = unquote(target.fragment)
        key = path.relative_to(root).as_posix()
        if fragment and key in pages and fragment not in pages[key].ids:
            errors.append(f'{source}: missing anchor {ref}')
    feed = root / 'feed.xml'
    if feed.exists():
        try:
            tree = ET.parse(feed)
            for element in tree.findall('.//link') + tree.findall('.//guid'):
                if urlsplit(element.text or '').scheme != 'https':
                    errors.append('feed.xml: link/guid must be an absolute HTTPS URL')
            atom = tree.find('.//{http://www.w3.org/2005/Atom}link')
            if atom is None or urlsplit(atom.attrib.get('href', '')).scheme != 'https':
                errors.append('feed.xml: self link must be an absolute HTTPS URL')
        except ET.ParseError as error:
            errors.append(f'feed.xml: malformed XML: {error}')
    return {'pages': len(pages), 'references': len(references),
            'errors': sorted(set(errors)), 'external_urls': sorted(external)}


def check_external(url):
    try:
        # GET avoids the many sites that reject HEAD while serving the page.
        request = Request(url, headers={'User-Agent': 'SirixWebsiteLinkCheck/1.0'})
        with urlopen(request, timeout=20) as response:
            return {'url': url, 'status': response.status, 'final_url': response.url}
    except HTTPError as error:
        return {'url': url, 'status': error.code, 'error': str(error)}
    except (URLError, TimeoutError, OSError) as error:
        return {'url': url, 'status': None, 'error': str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path)
    parser.add_argument('--external', action='store_true')
    args = parser.parse_args()
    if not args.site.is_dir():
        parser.error('site must be an existing build directory')
    result = check_site(args.site)
    if args.external:
        with ThreadPoolExecutor(max_workers=8) as executor:
            result['external_results'] = list(executor.map(check_external, result['external_urls']))
    print(json.dumps(result, indent=2))
    external_failures = any(item['status'] is None or item['status'] >= 400
                            for item in result.get('external_results', []))
    return 1 if result['errors'] or external_failures else 0


if __name__ == '__main__':
    sys.exit(main())
