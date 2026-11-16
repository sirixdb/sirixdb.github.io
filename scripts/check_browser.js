// Run at desktop and 390px against a locally served Jekyll build:
// chrome-devtools-axi run < scripts/check_browser.js
// The preview server must listen on 127.0.0.1:4188.
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
await page.open('http://127.0.0.1:4188/docs/index.html');
assert(await page.eval(() => document.querySelector('.docs-nav [aria-current="page"]')?.getAttribute('href') === '/docs/index.html'), 'Introduction is marked as the current documentation page');
await page.open('http://127.0.0.1:4188/docs/getting-started.html');
await page.eval(async () => { await document.fonts.ready; return true; });
const headerLayout = await page.eval(() => {
  const table = document.querySelector('.docs-content table');
  const shortHeaders = [...table.querySelectorAll('th')].filter(cell => /^\S{1,10}$/.test(cell.textContent.trim()));
  return {fits: document.documentElement.scrollWidth <= innerWidth && table.getBoundingClientRect().right <= innerWidth,
    headers: shortHeaders.map(cell => {
      const range = document.createRange();
      range.selectNodeContents(cell);
      return {text: cell.textContent.trim(), lines: range.getClientRects().length};
    })};
});
assert(headerLayout.fits, 'Getting Started table fits without horizontal page scrolling');
assert(headerLayout.headers.some(header => header.text === 'Time'), 'Time header is present');
assert(headerLayout.headers.every(header => header.lines === 1), 'Short table headers never break mid-word');
await page.open('http://127.0.0.1:4188/docs/architecture.html');
const mobile = await page.eval(() => innerWidth <= 768);
if (mobile) {
  assert(await page.eval(() => !document.querySelector('#site-nav').getClientRects().length), 'Closed mobile navigation must be hidden');
  assert(await page.eval(() => !document.querySelector('.docs-navigation').open), 'Mobile documentation index starts compact');
  await page.click('.docs-nav__toggle');
  assert(await page.eval(() => document.querySelector('.docs-navigation').open), 'Documentation index expands');
  await page.click('.docs-nav__toggle');
  await page.click('#menu-toggle');
  assert(await page.eval(() => document.querySelector('#menu-toggle').getAttribute('aria-expanded') === 'true'), 'Menu button exposes open state');
  await page.press('Escape');
  assert(await page.eval(() => document.activeElement.id === 'menu-toggle' && !document.querySelector('#site-nav').getClientRects().length), 'Escape closes menu and restores focus');
}
await page.eval(() => document.querySelector('.skip-link').focus());
await page.press('Enter');
assert(await page.eval(() => document.activeElement.id === 'main-content'), 'Skip link focuses main content');
await page.open('http://127.0.0.1:4188/docs/transactional-cursor-api.html');
assert(await page.eval(() => !!document.querySelector('.diagram-frame svg [id]')), 'Source diagram has inline IDs');
await page.eval(() => document.querySelector('.diagram-frame:has(svg [id]) .diagram-frame__expand').focus());
await page.press('Enter');
assert(await page.eval(() => document.querySelector('.svg-lightbox.is-open')?.contains(document.activeElement)), 'Keyboard opens diagram and focuses dialog');
assert(await page.eval(() => !!document.querySelector('.svg-lightbox.is-open .svg-lightbox__content [id]')), 'Expanded clone has inline IDs');
assert(await page.eval(() => {
  const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
  return ids.length === new Set(ids).size;
}), 'Mounted diagram clone keeps document IDs unique');
await page.press('Tab');
assert(await page.eval(() => document.querySelector('.svg-lightbox').contains(document.activeElement)), 'Dialog retains keyboard focus');
await page.press('Escape');
assert(await page.eval(() => document.activeElement.matches('.diagram-frame__expand') && !document.querySelector('.svg-lightbox.is-open')), 'Closing diagram restores trigger focus');
await page.open('http://127.0.0.1:4188/contact.html');
// Deliberately make third-party services unavailable; this test cannot send mail.
const fallback = await page.eval(() => {
  window.emailjs = undefined;
  window.grecaptcha = undefined;
  const submitted = document.querySelector('#contact-form').dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));
  return {prevented: !submitted, status: document.querySelector('#form-status').textContent};
});
assert(fallback.prevented && fallback.status.includes('email link above'), 'Blocked contact services give an accessible fallback without submitting');
assert(await page.eval(() => !!document.querySelector('a[href^="mailto:"]')), 'Contact fallback has a usable email link');
await page.open('http://127.0.0.1:4188/blog.html');
assert(await page.eval(() => !document.querySelector('.blog-card') && document.querySelector('.blog-empty')?.textContent.includes('The first post arrives with SirixDB 1.0')), 'Blog shows the future-release empty state without placeholder posts');
assert(await page.eval(() => !!document.querySelector('.site-footer a[href="/blog.html"]')), 'Blog navigation remains available');
const emptyFeed = await page.eval(async () => {
  const response = await fetch('/feed.xml');
  const feed = new DOMParser().parseFromString(await response.text(), 'application/xml');
  return {ok: response.ok, valid: !feed.querySelector('parsererror'), items: feed.querySelectorAll('item').length,
    home: feed.querySelector('channel > link')?.textContent,
    self: feed.getElementsByTagNameNS('http://www.w3.org/2005/Atom', 'link')[0]?.getAttribute('href')};
});
assert(emptyFeed.ok && emptyFeed.valid && emptyFeed.items === 0 && emptyFeed.home === 'https://sirix.io/' && emptyFeed.self === 'https://sirix.io/feed.xml', 'RSS remains valid and absolute with zero posts');
await page.open('http://127.0.0.1:4188/');
await page.eval(async () => { await document.fonts.ready; return true; });
const hero = await page.eval(() => {
  const kicker = document.querySelector('.lp-hero__kicker');
  const range = document.createRange();
  range.selectNodeContents(kicker);
  const lines = new Set([...range.getClientRects()].map(rect => Math.round(rect.top)));
  const pillars = document.querySelector('.pillars').getBoundingClientRect();
  const analytics = document.querySelector('.pillars a[href="#measured"]');
  const box = analytics.getBoundingClientRect();
  return {fits: document.documentElement.scrollWidth <= innerWidth,
    kickerFits: innerWidth <= 900 || lines.size === 1,
    balanced: Math.abs(box.width - pillars.width) < 1,
    target: !!document.querySelector(analytics.getAttribute('href'))};
});
assert(hero.fits && hero.kickerFits && hero.balanced, 'Hero fits the viewport, desktop kicker stays on one line, and final pillar fills its row');
assert(hero.target, 'Fast analytics pillar links to its benchmark evidence');
const explainer = await page.eval(() => {
  const video = document.querySelector('#watch video');
  if (!video) return null;
  const track = video.querySelector('track');
  const box = video.getBoundingClientRect();
  return {controls: video.controls, preload: video.getAttribute('preload'), autoplay: video.autoplay, inline: video.playsInline,
    poster: !!video.poster, source: video.querySelector('source')?.getAttribute('type'),
    track: track && {kind: track.kind, lang: track.srclang, isDefault: track.default},
    fits: box.left >= 0 && box.right <= innerWidth && document.documentElement.scrollWidth <= innerWidth,
    ratio: Math.round(box.width / box.height * 100) / 100, focusable: video.tabIndex >= 0,
    fetchedMedia: performance.getEntriesByType('resource').some(entry => /\.mp4($|\?)/.test(entry.name))};
});
assert(explainer, 'Landing page has the explainer video');
assert(explainer.controls && explainer.preload === 'none' && !explainer.autoplay && explainer.inline, 'Explainer video has controls, no autoplay, preload none and plays inline');
assert(explainer.poster && explainer.source === 'video/mp4', 'Explainer video has a poster and an MP4 source');
assert(explainer.track && explainer.track.kind === 'captions' && explainer.track.lang === 'en' && !explainer.track.isDefault, 'Explainer captions track is English and off by default');
assert(explainer.fits && explainer.ratio === 1.78, 'Explainer video keeps 16:9 inside the viewport without horizontal scrolling');
assert(explainer.focusable, 'Explainer video is reachable by keyboard');
assert(!explainer.fetchedMedia, 'Explainer video does not download before play');
// Follow the public contribution entry point through the real responsive menu.
if (mobile) await page.click('#menu-toggle');
await page.click('#site-nav a[href="/docs/get-involved.html"]');
await page.wait('.docs-content__title');
assert(await page.eval(() => location.pathname === '/docs/get-involved.html' && document.querySelector('h1')?.textContent === 'Get involved'), 'Header opens the contribution page');
assert(await page.eval(() => document.querySelector('#site-nav [aria-current="page"]')?.getAttribute('href') === location.pathname), 'Contribution page is current in the header');
assert(await page.eval(() => document.documentElement.scrollWidth <= innerWidth), 'Contribution page fits the viewport');
assert(await page.eval(() => !!document.querySelector('.site-footer a[href="/docs/get-involved.html"]')), 'Footer offers the contribution page');
if (mobile) {
  assert(await page.eval(() => !document.querySelector('#site-nav').getClientRects().length), 'Contribution page starts with the mobile menu closed');
  await page.click('#menu-toggle');
  assert(await page.eval(() => {
    const link = document.querySelector('#site-nav a[href="/docs/get-involved.html"]');
    const box = link.getBoundingClientRect();
    return box.width > 0 && box.left >= 0 && box.right <= innerWidth;
  }), 'Get involved remains visible inside the expanded phone menu');
  await page.click('#menu-toggle');
}
console.log(JSON.stringify({viewport: mobile ? 'phone' : 'desktop', navigation: 'pass', skipLink: 'pass', diagram: 'pass', blockedContact: 'pass', shortHeaders: 'pass', emptyBlog: 'pass', emptyFeed: 'pass', explainerVideo: 'pass', getInvolved: 'pass'}));
