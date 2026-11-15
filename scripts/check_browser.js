// Run at desktop and 390px against a locally served Jekyll build:
// chrome-devtools-axi run < scripts/check_browser.js
// The preview server must listen on 127.0.0.1:4188.
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
await page.open('http://127.0.0.1:4188/docs/index.html');
assert(await page.eval(() => document.querySelector('.docs-nav [aria-current="page"]')?.getAttribute('href') === '/docs/index.html'), 'Introduction is marked as the current documentation page');
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
console.log(JSON.stringify({viewport: mobile ? 'phone' : 'desktop', navigation: 'pass', skipLink: 'pass', diagram: 'pass', blockedContact: 'pass'}));
