# SirixDB Website

Source for [sirix.io](https://sirix.io) — the website for SirixDB, an open-source bitemporal document store.

Built with Jekyll 4 and hosted on GitHub Pages.

## Local Development

```bash
bundle exec jekyll serve
```

## Stack

- Jekyll 4 (static site generator)
- Vanilla CSS with custom properties (no preprocessor)
- Vanilla JavaScript (no dependencies)
- Google Fonts (Inter, JetBrains Mono)

## License

See [LICENSE.txt](LICENSE.txt) for the website license.

## Website checks

Before changing a page, identify the intended behavior and check its API/configuration
claims against the corresponding Sirix source. Preserve historical blog text. Cite
competitor and benchmark claims or remove them, and distinguish planned features
from current behavior.

```bash
bundle install
bundle exec jekyll build
python3 -m unittest discover -s tests -v
python3 scripts/check_site.py _site
# Network-dependent audit; rate limits and bot challenges remain unresolved:
python3 scripts/check_site.py _site --external
```

The PR check builds the actual output and verifies internal destinations/anchors,
image alternatives, heading structure and absolute RSS URLs. Seeded-defect tests
mutate valid fixtures (broken anchors/assets, duplicate IDs, heading gaps and relative
feed URLs) so regressions in the checker cannot silently turn these failures green.
These targeted mutation tests are not a general mutation-coverage measurement.

Explore changed pages in a browser at desktop and 390px width. Check keyboard
navigation, closed mobile menus, scrollable tables/code, diagram dialogs and the
contact form with blocked third-party scripts. With the preview served at port
4188, run `chrome-devtools-axi run < scripts/check_browser.js` at both widths to
repeat the navigation, skip-link, dialog-focus and blocked-contact regression checks.
Record observed bugs and keep a
regression check for each reproducible failure. External-link failures require
manual review; CI uses the deterministic internal check.
