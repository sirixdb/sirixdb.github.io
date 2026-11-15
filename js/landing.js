/* SirixDB landing page: animated diagrams and tabs for index.html.
   Plain JS, no dependencies. Animations run only while visible and never
   auto-play under prefers-reduced-motion; every diagram has manual controls. */
(function () {
  'use strict';
  var lp = document.querySelector('.lp');
  if (!lp || !('IntersectionObserver' in window)) return;
  lp.classList.add('lp--js');
  var mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  function still() { return mqReduce.matches; }
  var NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent, text) {
    var n = document.createElementNS(NS, tag);
    for (var a in attrs) n.setAttribute(a, attrs[a]);
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  }

  /* ---------- visibility-driven loops ---------- */
  var loops = [];
  function Loop(target, steps, interval, onStep, finalStep) {
    this.target = target; this.steps = steps; this.interval = interval; this.onStep = onStep; this.finalStep = finalStep;
    this.i = 0; this.timer = null; this.visible = false; this.userStopped = false;
    loops.push(this);
  }
  Loop.prototype.tick = function () { this.onStep(this.steps[this.i % this.steps.length]); this.i++; };
  Loop.prototype.start = function () {
    var self = this; this.stop();
    if (still() || this.userStopped || !this.visible) { if (still()) this.onStep(this.finalStep); return; }
    this.tick();
    this.timer = setInterval(function () { self.tick(); }, this.interval);
  };
  Loop.prototype.stop = function () { if (this.timer) clearInterval(this.timer); this.timer = null; };
  Loop.prototype.halt = function () { this.userStopped = true; this.stop(); };
  function restartAll() { loops.forEach(function (l) { l.start(); }); }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      loops.forEach(function (l) { if (l.target === en.target) { l.visible = en.isIntersecting; if (en.isIntersecting) l.start(); else l.stop(); } });
      if (en.isIntersecting && en.target.classList.contains('reveal')) en.target.classList.add('is-in');
    });
  }, { threshold: 0.25 });
  document.querySelectorAll('.reveal').forEach(function (n) { io.observe(n); });
  mqReduce.addEventListener && mqReduce.addEventListener('change', restartAll);

  /* ---------- Overview: evolution of state ---------- */
  function buildEvo(svg) {
    var g = svg.querySelector('.evo-g'), pre = svg.id;
    var COLS = [90, 240, 400, 560], BW = 96, BY = 105, BH = 140;
    var ROW_Y = [132, 152, 172, 192, 212], ROW_W = [72, 72, 50, 72, 58];
    var CHANGED = [[0, 1, 2, 3, 4], [1], [2, 3], [0]];   // pages written by each revision
    el('line', { 'class': 'axis', x1: 40, y1: 55, x2: 640, y2: 55 }, g);
    el('polygon', { points: '645,55 635,50 635,60', style: 'fill:var(--muted)' }, g);
    el('text', { 'class': 't-time', x: 340, y: 32, 'text-anchor': 'middle' }, g, 'TIME');
    var revs = [];
    COLS.forEach(function (cx, r) {
      var rg = el('g', { 'class': 'rev', id: pre + '-rev-' + (r + 1) }, g);
      el('title', {}, rg, 'Revision ' + (r + 1) + ': writes ' + CHANGED[r].length + (CHANGED[r].length === 1 ? ' page fragment' : ' page fragments') + ' plus the index pages on the path to its new root' + (r ? ', shares ' + (5 - CHANGED[r].length) : ''));
      el('line', { 'class': 'tick', x1: cx, y1: 43, x2: cx, y2: 67 }, rg);
      el('text', { 'class': 't-rev', x: cx, y: 88, 'text-anchor': 'middle' }, rg, 'Rev ' + (r + 1));
      if (r > 0) {
        var px = COLS[r - 1];
        ROW_Y.forEach(function (ry, i) {
          if (CHANGED[r].indexOf(i) < 0) el('line', { 'class': 'ptr', x1: px - 36 + ROW_W[i], y1: ry + 7, x2: cx - 36, y2: ry + 7 }, rg);
        });
        var ax0 = px + BW / 2 + 8, ax1 = cx - BW / 2 - 8;
        el('path', { 'class': 'edit', d: 'M' + ax0 + ',175 L' + ax1 + ',175', 'marker-end': 'url(#' + pre + '-arrow)' }, rg);
        el('text', { 'class': 't-edit', x: (ax0 + ax1) / 2, y: 167, 'text-anchor': 'middle' }, rg, 'edit');
      }
      el('rect', { 'class': 'box', x: cx - BW / 2, y: BY, width: BW, height: BH, rx: 10 }, rg);
      el('rect', { 'class': 'row-chg', x: cx - 18, y: BY - 4, width: 36, height: 8, rx: 3 }, rg);  // new revision root + index path
      el('text', { 'class': 't-state', x: cx, y: 123, 'text-anchor': 'middle' }, rg, 'STATE');
      ROW_Y.forEach(function (ry, i) {
        var chg = CHANGED[r].indexOf(i) >= 0;
        el('rect', { 'class': chg ? 'row-chg' : 'row-shr', x: cx - 36, y: ry, width: ROW_W[i], height: 14, rx: 4 }, rg);
      });
      el('text', { 'class': 't-snap', x: cx, y: 268, 'text-anchor': 'middle' }, rg, 'Snapshot');
      revs.push(rg);
    });
    var cap = el('text', { 'class': 't-cap', x: 340, y: 300, 'text-anchor': 'middle' }, g, '');
    el('rect', { 'class': 'row-chg', x: 110, y: 326, width: 18, height: 10, rx: 3 }, g);
    el('text', { 'class': 't-leg', x: 136, y: 336 }, g, 'Changed page-fragment');
    el('rect', { 'class': 'row-shr', x: 370, y: 326, width: 18, height: 10, rx: 3, style: 'fill-opacity:.35' }, g);
    el('text', { 'class': 't-leg', x: 396, y: 336 }, g, 'Shared (copy-on-write)');
    el('line', { 'class': 'ptr', x1: 110, y1: 358, x2: 150, y2: 358, style: 'opacity:.9' }, g);
    el('text', { 'class': 't-leg', x: 158, y: 362 }, g, 'Pointer to shared data');
    el('rect', { 'class': 'row-chg', x: 370, y: 353, width: 18, height: 8, rx: 3 }, g);
    el('text', { 'class': 't-leg', x: 396, y: 362 }, g, 'New root + index path');
    var CAPS = ['rev 1 · writes every page and its index tree', 'rev 2 · writes 1 fragment + root path, shares 4', 'rev 3 · writes 2 fragments + root paths, shares 3', 'rev 4 · writes 1 fragment + root path, shares 4', 'any snapshot opens directly · no replay'];
    function show(n) {
      revs.forEach(function (rg, i) {
        rg.classList.toggle('is-hidden', i >= Math.min(n, 4));
        rg.querySelectorAll('.row-chg').forEach(function (x) { x.classList.remove('pulse'); });
      });
      if (n <= 4 && !still()) { void revs[n - 1].getBoundingClientRect(); revs[n - 1].querySelectorAll('.row-chg').forEach(function (x) { x.classList.add('pulse'); }); }
      cap.textContent = CAPS[n - 1];
    }
    new Loop(svg, [1, 2, 3, 4, 5, 5], 1600, show, 5);
    show(5);
    io.observe(svg);
  }
  document.querySelectorAll('svg.evo-fig').forEach(buildEvo);

  /* ---------- Hero A: revision stack ---------- */
  (function () {
    var g = document.getElementById('layers');
    if (!g) return;
    // Each slab is an isometric rhombus: left vertex L, axis U to the top vertex, axis V to the bottom vertex.
    // Tiles are cells of a COLS x ROWS grid in slab coordinates (a along U, b along V), so they share the slab's perspective.
    var N = 5, cx = 210, baseY = 412, gap = 70, w = 170, h = 44;
    var COLS = 3, ROWS = 2, PAD = 0.07, GUT = 0.05;
    var changed = [null, 2, 5, 1, 4];  // cell written by revisions 2..5 (rev 1 writes every cell)
    function pt(y, a, b) { return [(cx - w) + a * w + b * w, y + a * -h + b * h]; }
    function cell(y, i) {
      var c = i % COLS, r = Math.floor(i / COLS);
      var cw = (1 - 2 * PAD - (COLS - 1) * GUT) / COLS, rh = (1 - 2 * PAD - (ROWS - 1) * GUT) / ROWS;
      var a0 = PAD + c * (cw + GUT), a1 = a0 + cw, b0 = PAD + r * (rh + GUT), b1 = b0 + rh;
      var q = [pt(y, a0, b0), pt(y, a1, b0), pt(y, a1, b1), pt(y, a0, b1)];
      return 'M' + q.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join(' L') + ' Z';
    }
    var layers = [];
    for (var r = 0; r < N; r++) {
      var y = baseY - r * gap;
      var lg = el('g', { 'class': 'layer', id: 'layer-' + (r + 1) }, g);
      el('title', {}, lg, r === 0 ? 'Revision 1: every page written' : 'Revision ' + (r + 1) + ': one changed fragment and the index pages on its path to the root written, the other pages shared');
      el('path', { 'class': 'layer-fill', d: 'M' + (cx - w) + ' ' + y + ' L' + cx + ' ' + (y - h) + ' L' + (cx + w) + ' ' + y + ' L' + cx + ' ' + (y + h) + ' Z' }, lg);
      for (var t = 0; t < COLS * ROWS; t++) {
        var cls = r === 0 ? 'tile tile--base' : (t === changed[r] ? 'tile tile--chg' : 'tile tile--ghost');
        el('path', { 'class': cls, d: cell(y, t) }, lg);
      }
      el('text', { 'class': 'lbl', x: cx + w + 12, y: y + 4 }, lg, 'rev ' + (r + 1));
      layers.push(lg);
    }
    var conn = document.getElementById('stack-conn');
    var q = document.getElementById('stack-q'), a = document.getElementById('stack-a');
    function show(step) {
      layers.forEach(function (l, i) { l.classList.toggle('is-on', i === step.on); });
      q.textContent = step.q; a.textContent = step.a;
      var y = baseY - step.on * gap;
      conn.setAttribute('d', 'M' + (cx + w - 20) + ' ' + (y - 6) + ' C ' + (cx + w + 30) + ' ' + (y - 50) + ', 400 140, 420 88');
    }
    var steps = [
      { on: 0, q: "commit → revision 1", a: 'writes every page and its index tree' },
      { on: 1, q: "commit → revision 2", a: 'writes 1 fragment + root path, shares rest' },
      { on: 2, q: "commit → revision 3", a: 'writes 1 fragment + root path, shares rest' },
      { on: 3, q: "commit → revision 4", a: 'writes 1 fragment + root path, shares rest' },
      { on: 4, q: "commit → revision 5", a: 'writes 1 fragment + root path, shares rest' },
      { on: 1, q: "jn:doc('shop','products', 2)", a: 'opens revision 2 directly · no replay' },
      { on: 1, q: "jn:doc('shop','products', 2)", a: 'opens revision 2 directly · no replay' }
    ];
    new Loop(document.getElementById('stack'), steps, 1500, show, steps[5]);
    io.observe(document.getElementById('stack'));
  })();

  /* ---------- Diagram 1: time travel ---------- */
  (function () {
    var REVS = {
      1: [['[', ''], ['  {"name": "Laptop", "price": 999},', 'ins'], ['  {"name": "Phone",  "price": 699}', 'ins'], [']', '']],
      2: [['[', ''], ['  {"name": "Laptop", "price": 899},', 'chg'], ['  {"name": "Phone",  "price": 699}', ''], [']', '']],
      3: [['[', ''], ['  {"name": "Laptop", "price": 899},', ''], ['  {"name": "Phone",  "price": 699},', ''], ['  {"name": "Tablet", "price": 449}', 'ins'], [']', '']],
      4: [['[', ''], ['  {"name": "Laptop", "price": 899},', ''], ['  {"name": "Phone",  "price": 699},', 'gone', 'deleted in rev 4'], ['  {"name": "Tablet", "price": 449}', ''], [']', '']]
    };
    var box = document.getElementById('tt'), doc = document.getElementById('tt-doc'), code = document.getElementById('tt-code'), badge = document.getElementById('tt-badge'), range = document.getElementById('tt-range');
    if (!box) return;
    var ticks = box.querySelectorAll('.tt__tick');
    function render(rev, jumped) {
      doc.innerHTML = '';
      REVS[rev].forEach(function (l) {
        var s = document.createElement('span'); s.className = 'ln ' + l[1];
        var body = document.createElement('span'); body.className = 'ln__body'; body.textContent = l[0]; s.appendChild(body);
        if (l[2]) { var n = document.createElement('span'); n.className = 'ln__note'; n.textContent = '  ← ' + l[2]; s.appendChild(n); }
        doc.appendChild(s);
      });
      ticks.forEach(function (t) { t.setAttribute('aria-pressed', String(+t.dataset.rev === rev)); });
      range.value = rev;
      code.textContent = "jn:doc('shop','products', " + rev + ")";
      badge.textContent = rev === 4 ? 'latest revision' : (jumped ? 'opened directly · same cost as latest' : 'revision ' + rev + ' · opened directly');
    }
    var steps = [{ r: 1 }, { r: 2 }, { r: 3 }, { r: 4 }, { r: 4 }, { r: 1, j: true }, { r: 1, j: true }];
    var loop = new Loop(box, steps, 1600, function (s) { render(s.r, s.j); }, { r: 4 });
    ticks.forEach(function (t) { t.addEventListener('click', function () { loop.halt(); render(+t.dataset.rev, true); }); });
    range.addEventListener('input', function () { loop.halt(); render(+range.value, true); });
    render(4);
    io.observe(box);
  })();

  /* ---------- Diagram 2: storage proportional to change ---------- */
  (function () {
    var svg = document.getElementById('st'), rowsG = document.getElementById('st-rows'), foot = document.getElementById('st-foot');
    if (!svg) return;
    var cols = [112, 192, 272, 352], W = 66, H = 62;
    // rows: for each revision, per page: 'full' | 'frag' | 'shared'
    var spec = [
      { label: 'rev 1', pages: ['full', 'full', 'full', 'full'], chg: [], bytes: 1, note: '4 pages + index' },
      { label: 'rev 2', pages: ['shared', 'frag', 'shared', 'shared'], chg: [1], bytes: 0.12, note: '1 record + path' },
      { label: 'rev 3', pages: ['shared', 'shared', 'shared', 'frag'], chg: [3], bytes: 0.12, note: '1 record + path' }
    ];
    var rows = [];
    spec.forEach(function (r, ri) {
      var y = 44 + ri * 106;
      var g = el('g', { 'class': 'row', id: 'st-row-' + (ri + 1) }, rowsG);
      el('title', {}, g, r.label + ': ' + r.note);
      el('text', { 'class': 't-h', x: 0, y: y + H / 2 + 5 }, g, r.label);
      r.pages.forEach(function (kind, pi) {
        var x = cols[pi] - W / 2;
        if (kind === 'shared') {
          el('rect', { 'class': 'ghost', x: x, y: y, width: W, height: H, rx: 8 }, g);
          // pointer up to where the page lives
          el('path', { 'class': 'ptr', d: 'M' + cols[pi] + ' ' + (y - 2) + ' V' + (y - 40) }, g);
          el('text', { 'class': 't-m', x: cols[pi], y: y + H / 2 + 4, 'text-anchor': 'middle' }, g, 'shared');
        } else {
          el('rect', { 'class': kind === 'frag' ? 'page page--frag' : 'page', x: x, y: y, width: W, height: H, rx: 8 }, g);
          for (var d = 0; d < 4; d++) {
            var dx = x + 19 + (d % 2) * 28, dy = y + 20 + Math.floor(d / 2) * 22;
            if (kind === 'frag') {
              if (d === 1) { el('circle', { 'class': 'rec rec--chg pulse', cx: dx, cy: dy, r: 6 }, g); }
              else { el('circle', { cx: dx, cy: dy, r: 5, fill: 'none', stroke: 'currentColor', 'stroke-dasharray': '2 3', style: 'color:var(--border-strong)' }, g); }
            } else {
              el('circle', { 'class': 'rec', cx: dx, cy: dy, r: 5 }, g);
            }
          }
          if (kind === 'frag') {
            el('text', { 'class': 't-m', x: cols[pi], y: y + H + 15, 'text-anchor': 'middle' }, g, 'fragment');
            // copy-on-write path: index pages from this leaf up to the new revision root
            el('path', { 'class': 'ptr', d: 'M' + cols[pi] + ' ' + (y - 2) + ' V' + (y - 34), style: 'stroke:var(--orange);stroke-dasharray:none' }, g);
            el('rect', { 'class': 'page page--frag', x: cols[pi] - 9, y: y - 16, width: 18, height: 10, rx: 2 }, g);
            el('rect', { 'class': 'page page--frag', x: cols[pi] - 9, y: y - 32, width: 18, height: 10, rx: 2 }, g);
            el('text', { 'class': 't-m', x: cols[pi] + 14, y: y - 18 }, g, 'path');
          }
        }
      });
      el('rect', { 'class': 'bar-bg', x: 410, y: y + 18, width: 165, height: 20, rx: 4 }, g);
      el('rect', { 'class': r.bytes < 1 ? 'bar bar--small' : 'bar', x: 410, y: y + 18, width: Math.max(9, 165 * r.bytes), height: 20, rx: 4 }, g);
      el('text', { 'class': 't-m', x: 410, y: y + 58 }, g, r.note);
      rows.push(g);
    });
    var chips = document.querySelectorAll('[data-st]');
    function show(n) {
      rows.forEach(function (g, i) { g.classList.toggle('is-hidden', i >= n); g.classList.toggle('is-live', i === n - 1 && n > 1); });
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(+c.dataset.st === n)); });
      foot.style.opacity = n === 3 ? 1 : 0;
    }
    var loop = new Loop(svg, [1, 2, 3, 3, 3], 1700, show, 3);
    chips.forEach(function (c) { c.addEventListener('click', function () { loop.halt(); show(+c.dataset.st); }); });
    document.getElementById('st-play').addEventListener('click', function () { loop.userStopped = false; loop.i = 0; loop.start(); });
    show(3);
    io.observe(svg);
  })();

  /* ---------- Diagram 3: node-level diff ---------- */
  (function () {
    var svg = document.getElementById('df'), g = document.getElementById('df-g'), out = document.getElementById('df-out');
    if (!svg) return;
    function node(x, y, w, label, key, cls, id) {
      var n = el('g', { 'class': 'node ' + (cls || ''), id: id }, g);
      el('title', {}, n, label + ' (node ' + key + ')');
      el('rect', { x: x, y: y, width: w, height: 30, rx: 7 }, n);
      el('text', { x: x + 10, y: y + 20 }, n, label);
      el('text', { 'class': 'key', x: x + w - 8, y: y + 20, 'text-anchor': 'end' }, n, '#' + key);
      return { x: x, y: y, w: w };
    }
    function edge(a, b) { el('path', { 'class': 'edge', d: 'M' + (a.x + 14) + ' ' + (a.y + 28) + ' V' + (b.y + 14) + ' H' + b.x }, g); }
    // rev 1 tree
    var L = 4, R = 362;
    var a1 = node(L, 44, 74, '[ ]', 1, '', 'df-l-1');
    var o2 = node(L + 24, 84, 70, '{ }', 2, '', 'df-l-2');
    // node keys from a real run of this catalog (sdb:nodekey, SirixDB 1.0.0-beta7)
    var n4 = node(L + 48, 122, 220, 'name: "Laptop"', 3, '', 'df-l-3');
    var p6 = node(L + 48, 156, 220, 'price: 999', 4, 'upd', 'df-l-4');
    var o7 = node(L + 24, 198, 70, '{ }', 5, 'del', 'df-l-5');
    var n9 = node(L + 48, 236, 220, 'name: "Phone"', 6, 'del', 'df-l-6');
    var p11 = node(L + 48, 270, 220, 'price: 699', 7, 'del', 'df-l-7');
    edge(a1, o2); edge(o2, n4); edge(o2, p6); edge(a1, o7); edge(o7, n9); edge(o7, p11);
    // rev 4 tree
    var b1 = node(R, 44, 74, '[ ]', 1, '', 'df-r-1');
    var q2 = node(R + 24, 84, 70, '{ }', 2, '', 'df-r-2');
    var m4 = node(R + 48, 122, 220, 'name: "Laptop"', 3, '', 'df-r-3');
    var r6 = node(R + 48, 156, 220, 'price: 899', 4, 'upd', 'df-r-4');
    var q12 = node(R + 24, 198, 70, '{ }', 8, 'ins', 'df-r-8');
    var m14 = node(R + 48, 236, 220, 'name: "Tablet"', 9, 'ins', 'df-r-9');
    var r16 = node(R + 48, 270, 220, 'price: 449', 10, 'ins', 'df-r-10');
    edge(b1, q2); edge(q2, m4); edge(q2, r6); edge(b1, q12); edge(q12, m14); edge(q12, r16);
    // identity lines: same node key across revisions
    [[a1, b1], [o2, q2], [n4, m4], [p6, r6]].forEach(function (p) {
      var x1 = p[0].x + p[0].w, y1 = p[0].y + 14, x2 = p[1].x, y2 = p[1].y + 14;
      var path = el('path', { 'class': 'ident', d: 'M' + x1 + ' ' + y1 + ' C ' + (x1 + 30) + ' ' + y1 + ', ' + (x2 - 30) + ' ' + y2 + ', ' + x2 + ' ' + y2 }, g);
      g.insertBefore(path, g.firstChild);
    });
    var ops = out.querySelectorAll('.op'), chips = document.querySelectorAll('[data-df]');
    function show(s) {
      svg.classList.toggle('show-ident', true);
      ['upd', 'ins', 'del'].forEach(function (k) { svg.classList.toggle('on-' + k, s === k || s === 'all'); });
      ops.forEach(function (o) { o.classList.toggle('on', s === 'all' || o.classList.contains(s)); });
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.df === s)); });
    }
    var loop = new Loop(svg, ['none', 'upd', 'ins', 'del', 'all', 'all'], 1500, show, 'all');
    chips.forEach(function (c) { c.addEventListener('click', function () { loop.halt(); show(c.dataset.df); }); });
    show('all');
    io.observe(svg);
  })();

  /* ---------- Diagram 4: bitemporal ---------- */
  (function () {
    var svg = document.getElementById('bt'), grid = document.getElementById('bt-grid');
    if (!svg) return;
    // Transaction time: Mar 1 at x=160, 30 px/day (Mar 10 = 430, today = Mar 15 = 580).
    // Valid time: Mar 1 at y=160, 12 px/day upwards (Mar 5 = 112, Feb 20 = 268).
    var X0 = 160, PX_DAY = 30, Y0 = 160, PY_DAY = 12, MOVE_RECORDED = 9 /* Mar 10 */, TODAY = 14 /* Mar 15 */;
    var MON = ['Jan', 'Feb', 'Mar', 'Apr'];
    function fmt(off) { var d = new Date(Date.UTC(2026, 2, 1) + off * 864e5); return MON[d.getUTCMonth()] + ' ' + d.getUTCDate(); }
    [{ off: 0, l: 'Mar 1' }, { off: 9, l: 'Mar 10' }, { off: 14, l: 'Mar 15' }].forEach(function (t) {
      var x = X0 + t.off * PX_DAY;
      el('line', { 'class': 'gridl', x1: x, y1: 320, x2: x, y2: 40 }, grid);
      el('text', { 'class': 't-m', x: x, y: 340, 'text-anchor': 'middle' }, grid, t.l);
    });
    [{ off: 0, l: 'Mar 1' }, { off: -9, l: 'Feb 20' }].forEach(function (v) {
      var y = Y0 - v.off * PY_DAY;
      el('line', { 'class': 'gridl', x1: 80, y1: y, x2: 610, y2: y }, grid);
      el('text', { 'class': 't-m', x: 72, y: y + 4, 'text-anchor': 'end' }, grid, v.l);
    });
    var q = document.getElementById('bt-q'), a = document.getElementById('bt-a'), why = document.getElementById('bt-why');
    var gv = document.getElementById('bt-v'), gh = document.getElementById('bt-h'), dot = document.getElementById('bt-dot'), ring = document.getElementById('bt-ring');
    var txl = document.getElementById('bt-txl'), vl = document.getElementById('bt-vl'), ans = document.querySelector('.bt-ans');
    var chips = document.querySelectorAll('[data-bt]');
    function xFor(off) { return X0 + off * PX_DAY; }
    function yFor(off) { return Y0 - off * PY_DAY; }
    var P = { a: { x: xFor(4), y: yFor(4) }, b: { x: xFor(TODAY), y: yFor(4) }, c: { x: xFor(TODAY), y: yFor(-9) } };
    var cur = { x: P.a.x, y: P.a.y }, anim = null;
    function render(x, y) {
      var txOff = Math.floor((x - X0) / PX_DAY + 1e-6), vOff = Math.floor((Y0 - y) / PY_DAY + 1e-6);
      gv.setAttribute('transform', 'translate(' + x.toFixed(1) + ',0)');
      gh.setAttribute('transform', 'translate(0,' + y.toFixed(1) + ')');
      dot.setAttribute('cx', x.toFixed(1)); dot.setAttribute('cy', y.toFixed(1));
      ring.setAttribute('cx', x.toFixed(1)); ring.setAttribute('cy', y.toFixed(1));
      txl.textContent = fmt(txOff); vl.textContent = fmt(vOff);
      q.textContent = 'Recorded on ' + fmt(txOff) + (txOff === TODAY ? ' (today)' : '') + ', valid ' + fmt(vOff) + ':';
      var r;
      if (txOff < MOVE_RECORDED) r = ['Berlin', 'blue', 'rev 1 · the move was not reported yet'];
      else if (vOff < 0) r = ['Berlin', 'blue', 'rev 2 · she lived in Berlin until Mar 1'];
      else r = ['Munich', 'orange', 'rev 2 · move recorded Mar 10, effective Mar 1; rev 1 still says Berlin'];
      a.textContent = r[0]; a.className = 'a ' + r[1]; why.textContent = r[2];
    }
    function moveTo(k) {
      var from = { x: cur.x, y: cur.y }, to = P[k], t0 = null, DUR = 1500;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.bt === k)); });
      if (anim) cancelAnimationFrame(anim);
      if (still() || (from.x === to.x && from.y === to.y)) { cur = { x: to.x, y: to.y }; render(to.x, to.y); return; }
      ans.setAttribute('aria-busy', 'true');
      function frame(ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / DUR), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
        cur = { x: from.x + (to.x - from.x) * e, y: from.y + (to.y - from.y) * e }; render(cur.x, cur.y);
        if (p < 1) anim = requestAnimationFrame(frame); else { anim = null; ans.setAttribute('aria-busy', 'false'); }
      }
      anim = requestAnimationFrame(frame);
    }
    var loop = new Loop(svg, ['a', 'b', 'c'], 3200, moveTo, 'b');
    chips.forEach(function (c) { c.addEventListener('click', function () { loop.halt(); moveTo(c.dataset.bt); }); });
    render(cur.x, cur.y);
    io.observe(svg);
  })();

  /* ---------- Enterprise: replication ---------- */
  (function () {
    var svg = document.getElementById('rp'), cap = document.getElementById('rp-cap');
    if (!svg) return;
    var revL = document.getElementById('rp-rev-l'), revF = document.getElementById('rp-rev-f');
    var toks = [1, 2, 3, 4].map(function (i) { return document.getElementById('rp-' + i); });
    var S = [
      { on: [], l: 41, f: 41, c: 'steady state: leader and follower both at rev 41' },
      { on: [0], l: 42, f: 41, c: '1 · leader commits rev 42, uploads segment + manifest to S3' },
      { on: [1], l: 42, f: 41, c: '2 · leader publishes one small commit event' },
      { on: [2], l: 42, f: 41, c: '3 · follower consumes the event, in order' },
      { on: [3], l: 42, f: 42, c: '4 · follower reloads the manifest from S3 and serves rev 42' },
      { on: [], l: 42, f: 42, c: 'both at rev 42 · page data stored once, in S3' }
    ];
    function show(s) {
      toks.forEach(function (t, i) { t.classList.toggle('step-on', s.on.indexOf(i) >= 0); });
      revL.textContent = 'rev ' + s.l; revF.textContent = 'rev ' + s.f; cap.textContent = s.c;
    }
    new Loop(svg, S, 1700, show, S[5]);
    show(S[5]);
    io.observe(svg);
  })();

  /* ---------- Diagram 6: agents ---------- */
  (function () {
    var svg = document.getElementById('ag'), g = document.getElementById('ag-g'), cap = document.getElementById('ag-cap');
    if (!svg) return;
    function rev(x, label, sub, chg, id) {
      var r = el('g', { 'class': 'step', id: id }, g);
      el('title', {}, r, label + ' ' + sub);
      el('rect', { 'class': 'box', x: x, y: 90, width: 110, height: 110, rx: 10 }, r);
      el('text', { 'class': 't', x: x + 55, y: 82, 'text-anchor': 'middle' }, r, label);
      for (var i = 0; i < 4; i++) el('rect', { 'class': chg.indexOf(i) >= 0 ? 'row row--chg' : 'row', x: x + 14, y: 106 + i * 22, width: [82, 82, 60, 70][i], height: 13, rx: 3 }, r);
      el('text', { 'class': 't-s', x: x + 55, y: 222, 'text-anchor': 'middle' }, r, sub);
      // lock = immutable
      el('rect', { 'class': 'lock', x: x + 92, y: 70, width: 12, height: 9, rx: 2 }, r);
      el('path', { 'class': 'lock', d: 'M' + (x + 94.5) + ' 70 v-3 a3.5 3.5 0 0 1 7 0 v3' }, r);
      return r;
    }
    var s1 = rev(10, 'rev 41', 'before', [], 'ag-s1');
    var s2 = el('g', { 'class': 'step', id: 'ag-s2' }, g);
    el('rect', { 'class': 'box box--agent', x: 132, y: 20, width: 70, height: 30, rx: 8 }, s2);
    el('text', { 'class': 't-s', x: 167, y: 40, 'text-anchor': 'middle', style: 'fill:var(--orange-text);font-weight:700' }, s2, 'agent');
    el('path', { 'class': 'arrow arrow--o', d: 'M124 145 H164', 'marker-end': 'url(#ag-aho)' }, s2);
    el('path', { 'class': 'arrow arrow--o', d: 'M167 52 V138', style: 'stroke-dasharray:3 3' }, s2);
    var r42 = rev(172, 'rev 42', 'agent edit', [1, 3], 'ag-s2b');
    var s3 = el('g', { 'class': 'step', id: 'ag-s3' }, g);
    el('path', { 'class': 'arrow', d: 'M286 145 H318', 'marker-end': 'url(#ag-ah)' }, s3);
    el('rect', { 'class': 'box box--diff', x: 322, y: 90, width: 150, height: 110, rx: 10 }, s3);
    el('text', { 'class': 't', x: 397, y: 82, 'text-anchor': 'middle' }, s3, 'diff 41 → 42');
    el('text', { 'class': 't-d', x: 334, y: 122, style: 'fill:#F7924A' }, s3, 'update #6');
    el('text', { 'class': 't-d', x: 334, y: 148, style: 'fill:#6CC6F3' }, s3, 'insert #12');
    el('text', { 'class': 't-d', x: 334, y: 174, style: 'fill:#f2a3a3' }, s3, 'delete #7');
    var s4 = el('g', { 'class': 'step', id: 'ag-s4' }, g);
    el('path', { 'class': 'arrow', d: 'M476 145 H516', 'marker-end': 'url(#ag-ah)' }, s4);
    el('text', { 'class': 't-s', x: 496, y: 136, 'text-anchor': 'middle' }, s4, 'revert');
    var r43 = rev(522, 'rev 43', '= rev 41 content', [], 'ag-s4b');
    s4.appendChild(r43); r43.setAttribute('class', '');
    var groups = [s1, [s2, r42], s3, s4];
    var CAPS = ['rev 41 · current state', 'agent edits via MCP → rev 42 · rev 41 untouched',
                'inspect: structural diff 41 → 42 · three nodes changed', 'revert → appended as rev 43 · rev 42 stays in history',
                'every revision immutable · MCP calls audit-logged'];
    function show(n) {
      groups.forEach(function (gr, i) { [].concat(gr).forEach(function (x) { x.classList.toggle('is-hidden', i >= n); }); });
      cap.textContent = CAPS[Math.min(n, 5) - 1];
    }
    new Loop(svg, [1, 2, 3, 4, 5, 5], 1800, show, 5);
    show(5);
    io.observe(svg);
  })();

  /* ---------- tabs ---------- */
  (function () {
    var tabs = Array.prototype.slice.call(document.querySelectorAll('.tabs [role="tab"]'));
    if (!tabs.length) return;
    function select(t) {
      tabs.forEach(function (x) {
        var on = x === t;
        x.setAttribute('aria-selected', String(on)); x.tabIndex = on ? 0 : -1;
        document.getElementById(x.getAttribute('aria-controls')).hidden = !on;
      });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(t); });
      t.addEventListener('keydown', function (e) {
        var k = e.key, n = null;
        if (k === 'ArrowDown' || k === 'ArrowRight') n = tabs[(i + 1) % tabs.length];
        if (k === 'ArrowUp' || k === 'ArrowLeft') n = tabs[(i - 1 + tabs.length) % tabs.length];
        if (n) { e.preventDefault(); select(n); n.focus(); }
      });
    });
  })();
})();

/* ---------- See it in action: typed sirix-shell session ----------
   The full transcript is static HTML (_includes/landing-shell.html). This only
   replays it: clears the commands, types them token by token, then reveals the
   real output. Reduced motion, "Show all" or no JS = the static transcript. */
(function () {
  'use strict';
  var shell = document.getElementById('shell');
  if (!shell) return;
  var body = shell.querySelector('.shell__body');
  var steps = Array.prototype.slice.call(shell.querySelectorAll('.shell__step'));
  var pills = Array.prototype.slice.call(document.querySelectorAll('.shell-revs li'));
  var label = document.getElementById('shell-revs-label');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  // remember each command's highlighted tokens so typing keeps the colours
  var model = steps.map(function (st) {
    var code = st.querySelector('.shell__cmd code');
    var toks = Array.prototype.map.call(code.childNodes, function (n) {
      return { cls: n.nodeType === 1 ? n.className : '', text: n.textContent };
    });
    return { el: st, code: code, html: code.innerHTML, toks: toks, out: st.querySelector('.shell__out'),
             rev: JSON.parse(st.getAttribute('data-rev')) };
  });

  function revs(state) {
    var maxDone = state.done || 0;
    pills.forEach(function (li) {
      var r = +li.getAttribute('data-rev');
      li.classList.toggle('is-done', r <= maxDone);
      li.classList.toggle('is-on', state.write === r);
      li.classList.toggle('is-read', (state.read || []).indexOf(r) >= 0);
    });
    if (label) label.textContent = state.text;
  }
  function revsFor(rev, doneBefore) {
    if (rev.kind === 'write') return { done: rev.rev, write: rev.rev, text: rev.label };
    if (rev.kind === 'read') return { done: doneBefore, read: [rev.rev], text: rev.label };
    if (rev.kind === 'history') return { done: doneBefore, read: rev.revs, text: rev.label };
    if (rev.kind === 'diff') return { done: doneBefore, read: [rev.from, rev.to], text: rev.label };
    return { done: doneBefore, read: [1, 2, 3, 4], text: rev.label };
  }
  var restState = { done: 4, text: '4 immutable revisions' };

  var gen = 0, timers = [];
  function later(fn, ms, g) { timers.push(setTimeout(function () { if (g === gen) fn(); }, ms)); }
  function cancel() { gen++; timers.forEach(clearTimeout); timers = []; }
  function scrollEnd() { body.scrollTop = body.scrollHeight; }

  function showAll() {
    cancel();
    shell.classList.remove('is-anim');
    body.style.height = '';
    model.forEach(function (m) {
      m.code.innerHTML = m.html;
      m.el.classList.remove('is-pending'); m.out.classList.remove('is-pending', 'is-in');
    });
    revs(restState);
  }

  // natural cadence: quick letters, small pauses after spaces/punctuation, longer at line ends
  function delay(ch) {
    var base = 16 + Math.random() * 26;
    if (ch === '\n') return base + 220;
    if (/[\s,;]/.test(ch)) return base + 40;
    if (/[()\[\]{}]/.test(ch)) return base + 25;
    return base;
  }

  function typeStep(i, g, doneBefore) {
    if (i >= model.length) { later(function () { revs(restState); }, 1200, g); return; }
    var m = model[i];
    m.el.classList.remove('is-pending');
    m.code.innerHTML = '';
    var caret = document.createElement('span'); caret.className = 'shell__caret';
    m.code.appendChild(caret);
    var t = 0, c = 0, span = null;
    function next() {
      if (g !== gen) return;
      var tok = m.toks[t];
      if (!tok) { finish(); return; }
      if (c === 0) {
        span = tok.cls ? document.createElement('span') : document.createTextNode('');
        if (tok.cls) span.className = tok.cls;
        m.code.insertBefore(span, caret);
      }
      var ch = tok.text.charAt(c++);
      if (tok.cls) span.textContent += ch; else span.data += ch;
      if (c >= tok.text.length) { t++; c = 0; }
      if (ch === '\n') scrollEnd();
      later(next, delay(ch), g);
    }
    function finish() {
      later(function () {
        caret.remove();
        var st = revsFor(m.rev, doneBefore);
        revs(st);
        m.out.classList.remove('is-pending'); m.out.classList.add('is-in');
        scrollEnd();
        later(function () { typeStep(i + 1, g, st.done); }, 1100 + Math.min(1400, m.out.textContent.length * 4), g);
      }, 420, g);
    }
    scrollEnd();
    later(next, 380, g);
  }

  function play() {
    if (reduce.matches) { showAll(); return; }
    cancel();
    var g = gen;
    // keep the terminal's size while steps appear, so the page never jumps
    if (!shell.classList.contains('is-anim')) body.style.height = body.clientHeight + 'px';
    shell.classList.add('is-anim');
    model.forEach(function (m) { m.el.classList.add('is-pending'); m.out.classList.add('is-pending'); m.out.classList.remove('is-in'); });
    body.scrollTop = 0;
    revs({ done: 0, text: 'empty database' });
    later(function () { typeStep(0, g, 0); }, 500, g);
  }

  shell.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    if (b.getAttribute('data-shell') === 'replay') play();
    else if (b.getAttribute('data-shell') === 'all') showAll();
    else if (b.classList.contains('shell__copy')) {
      var txt = b.getAttribute('data-copy');
      var done = function () { b.textContent = 'copied'; b.classList.add('is-copied');
        setTimeout(function () { b.textContent = 'copy'; b.classList.remove('is-copied'); }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, function () {});
    }
  });

  revs(restState);
  if (reduce.matches || !('IntersectionObserver' in window)) return;
  var seen = false;
  new IntersectionObserver(function (entries, obs) {
    entries.forEach(function (en) {
      if (en.isIntersecting && !seen) { seen = true; obs.disconnect(); play(); }
    });
  }, { threshold: 0.3 }).observe(shell);
})();

/* ---------- See it in the browser: web interface carousel ---------- */
(function () {
  'use strict';
  var root = document.getElementById('gui-carousel');
  if (!root) return;
  var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
  var url = document.getElementById('gui-url');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var cur = 0, timer = null, paused = false, visible = false;
  function select(i, focus) {
    cur = (i + tabs.length) % tabs.length;
    tabs.forEach(function (t, k) {
      var on = k === cur, panel = document.getElementById(t.getAttribute('aria-controls'));
      t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1;
      panel.hidden = !on; panel.classList.toggle('is-in', on);
      if (on && url) url.textContent = panel.getAttribute('data-url');
    });
    if (focus) tabs[cur].focus();
  }
  function stop() { if (timer) clearInterval(timer); timer = null; }
  function start() {
    stop();
    if (reduce.matches || paused || !visible) return;
    timer = setInterval(function () { select(cur + 1); }, 5000);
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { paused = true; stop(); select(i); });
    t.addEventListener('keydown', function (e) {
      var d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (d) { e.preventDefault(); paused = true; stop(); select(cur + d, true); }
    });
  });
  root.addEventListener('mouseenter', stop);
  root.addEventListener('mouseleave', start);
  root.addEventListener('focusin', stop);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) start(); else stop(); }, { threshold: 0.4 }).observe(root);
  }
})();
