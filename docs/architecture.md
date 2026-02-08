---
layout: documentation
doctitle: Architecture
title: SirixDB - Architecture
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/architecture.md)

SirixDB is a temporal, append-only database that never overwrites data. Every transaction commit creates an immutable snapshot. It uses **copy-on-write with path copying** to share unchanged data between revisions, keeping storage minimal. The storage engine is log-structured and optimized for flash drives — sequential writes only, no WAL, no compaction.

## Node-Based Document Model

Unlike document databases that store JSON as opaque blobs, SirixDB decomposes each document into a tree of fine-grained **nodes**. Each node has a stable 64-bit `nodeKey` that never changes across revisions. Nodes are linked via parent, child, and sibling pointers, enabling O(1) navigation in any direction.

Field names are stored once in an in-memory dictionary and referenced by 32-bit keys, saving space when the same field appears thousands of times.

<svg viewBox="0 0 720 300" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="JSON document decomposed into a tree of nodes with stable node keys">
  <!-- Title -->
  <text x="360" y="20" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">JSON Tree Encoding</text>

  <!-- Source JSON -->
  <rect x="20" y="38" width="300" height="42" rx="6" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="1" opacity="0.6"/>
  <text x="30" y="55" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">Input JSON</text>
  <text x="30" y="72" fill="#42B6F0" font-size="11" font-family="JetBrains Mono,monospace">{"name":"Alice","scores":[95,87]}</text>

  <!-- Document root -->
  <rect x="330" y="45" width="60" height="28" rx="4" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="360" y="63" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">DOC</text>
  <text x="395" y="63" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=0</text>

  <!-- Object node -->
  <line x1="360" y1="73" x2="360" y2="102" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="326" y="102" width="68" height="26" rx="4" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="360" y="119" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">OBJECT</text>
  <text x="399" y="119" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=1</text>

  <!-- Left branch: "name" key -->
  <line x1="345" y1="128" x2="220" y2="165" stroke="#42B6F0" stroke-width="1"/>
  <rect x="170" y="165" width="100" height="24" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="220" y="181" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">OBJ_KEY "name"</text>
  <text x="275" y="181" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=2</text>

  <!-- "Alice" value -->
  <line x1="220" y1="189" x2="220" y2="215" stroke="#10b981" stroke-width="1"/>
  <rect x="175" y="218" width="90" height="22" rx="3" fill="rgba(16,185,129,0.1)" stroke="#10b981" stroke-width="1"/>
  <text x="220" y="233" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">STR "Alice"</text>
  <text x="270" y="233" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=3</text>

  <!-- Right branch: "scores" key -->
  <line x1="375" y1="128" x2="500" y2="165" stroke="#42B6F0" stroke-width="1"/>
  <rect x="445" y="165" width="110" height="24" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="500" y="181" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">OBJ_KEY "scores"</text>
  <text x="560" y="181" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=4</text>

  <!-- Array node -->
  <line x1="500" y1="189" x2="500" y2="215" stroke="#42B6F0" stroke-width="1"/>
  <rect x="465" y="218" width="70" height="22" rx="3" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="500" y="233" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">ARRAY</text>
  <text x="540" y="233" text-anchor="start" fill="#6b7280" font-size="8" font-family="JetBrains Mono,monospace">key=5</text>

  <!-- Array values -->
  <line x1="487" y1="240" x2="455" y2="265" stroke="#10b981" stroke-width="1"/>
  <rect x="425" y="265" width="60" height="20" rx="3" fill="rgba(16,185,129,0.1)" stroke="#10b981" stroke-width="1"/>
  <text x="455" y="279" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">NUM 95</text>
  <text x="420" y="279" text-anchor="end" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">key=6</text>

  <line x1="513" y1="240" x2="545" y2="265" stroke="#10b981" stroke-width="1"/>
  <rect x="515" y="265" width="60" height="20" rx="3" fill="rgba(16,185,129,0.1)" stroke="#10b981" stroke-width="1"/>
  <text x="545" y="279" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">NUM 87</text>
  <text x="580" y="279" text-anchor="start" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">key=7</text>

  <!-- Sibling link between array items -->
  <line x1="485" y1="275" x2="515" y2="275" stroke="#10b981" stroke-width="1"/>

  <!-- Legend -->
  <rect x="600" y="105" width="10" height="10" rx="2" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="616" y="114" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Structure node</text>
  <rect x="600" y="123" width="10" height="10" rx="2" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1"/>
  <text x="616" y="132" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Object key</text>
  <rect x="600" y="141" width="10" height="10" rx="2" fill="rgba(16,185,129,0.1)" stroke="#10b981" stroke-width="1"/>
  <text x="616" y="150" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Value node</text>
</svg>

Each node type maps directly to a JSON construct: `OBJECT`, `ARRAY`, `OBJECT_KEY`, `STRING_VALUE`, `NUMBER_VALUE`, `BOOLEAN_VALUE`, and `NULL_VALUE`. Navigation between nodes is O(1) via stored pointers — no scanning required.

## Copy-on-Write with Path Copying

When a transaction modifies data, SirixDB doesn't rewrite existing pages. Instead, it **copies only the modified page and its ancestor path** to the root. All unchanged pages are shared between the old and new revision via pointers. This is the same principle used in persistent data structures and ZFS.

<svg viewBox="0 0 720 260" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Copy-on-write: modifying a leaf copies only the path to root, sharing unchanged pages">

  <!-- Legend -->
  <rect x="20" y="8" width="12" height="12" rx="2" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="38" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">New page</text>
  <rect x="170" y="8" width="12" height="12" rx="2" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="188" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">Modified page</text>
  <line x1="320" y1="14" x2="360" y2="14" stroke="#6b7280" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>
  <text x="368" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">Shared pointer (unchanged)</text>

  <!-- === Rev 1 === -->
  <!-- UberPage (conceptual top, no trie to RevRoot) -->
  <rect x="107" y="38" width="46" height="20" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="130" y="52" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <line x1="130" y1="58" x2="130" y2="68" stroke="#42B6F0" stroke-width="1" stroke-dasharray="3 2"/>
  <!-- RevRootPage -->
  <rect x="97" y="70" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="130" y="85" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Data trie -->
  <line x1="115" y1="92" x2="80" y2="110" stroke="#42B6F0" stroke-width="1"/>
  <line x1="145" y1="92" x2="180" y2="110" stroke="#42B6F0" stroke-width="1"/>
  <rect x="52" y="112" width="56" height="18" rx="3" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="80" y="125" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Indirect</text>
  <rect x="152" y="112" width="56" height="18" rx="3" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="180" y="125" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Indirect</text>
  <!-- RecordPages -->
  <line x1="66" y1="130" x2="58" y2="147" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="94" y1="130" x2="102" y2="147" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="38" y="149" width="40" height="16" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="58" y="160" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page A</text>
  <rect x="82" y="149" width="40" height="16" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="102" y="160" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page B</text>
  <line x1="166" y1="130" x2="158" y2="147" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="194" y1="130" x2="202" y2="147" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="138" y="149" width="40" height="16" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="158" y="160" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page C</text>
  <rect x="182" y="149" width="40" height="16" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="202" y="160" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page D</text>

  <!-- === Rev 2: modify Page A, copy path === -->
  <rect x="347" y="38" width="46" height="20" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="370" y="52" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <line x1="370" y1="58" x2="370" y2="68" stroke="#42B6F0" stroke-width="1" stroke-dasharray="3 2"/>
  <rect x="337" y="70" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="370" y="85" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Left branch: copied (modified) -->
  <line x1="355" y1="92" x2="330" y2="110" stroke="#F47B20" stroke-width="1.2"/>
  <rect x="302" y="112" width="56" height="18" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="330" y="125" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Indirect'</text>
  <!-- Modified Page A' -->
  <line x1="316" y1="130" x2="306" y2="147" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="286" y="149" width="40" height="16" rx="2" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="306" y="160" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">Page A'</text>
  <!-- Shared pointer to Page B -->
  <line x1="344" y1="130" x2="122" y2="149" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Right branch: shared pointer to Rev1's right indirect -->
  <line x1="385" y1="92" x2="208" y2="121" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>

  <!-- === Rev 3: modify Page D, share rest === -->
  <rect x="557" y="38" width="46" height="20" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="580" y="52" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <line x1="580" y1="58" x2="580" y2="68" stroke="#42B6F0" stroke-width="1" stroke-dasharray="3 2"/>
  <rect x="547" y="70" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="580" y="85" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Left: share Rev2's left indirect -->
  <line x1="565" y1="92" x2="358" y2="121" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Right: modified -->
  <line x1="595" y1="92" x2="620" y2="110" stroke="#F47B20" stroke-width="1.2"/>
  <rect x="592" y="112" width="56" height="18" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="620" y="125" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Indirect'</text>
  <!-- Shared Page C -->
  <line x1="606" y1="130" x2="178" y2="149" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Modified Page D' -->
  <line x1="634" y1="130" x2="644" y2="147" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="624" y="149" width="40" height="16" rx="2" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="644" y="160" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">Page D'</text>

  <!-- Annotation -->
  <text x="306" y="182" text-anchor="middle" fill="#F47B20" font-size="8" font-family="Inter,sans-serif" font-style="italic">only changed path copied</text>

  <!-- Timeline -->
  <line x1="60" y1="210" x2="680" y2="210" stroke="#6b7280" stroke-width="1.5"/>
  <polygon points="680,210 670,205 670,215" fill="#6b7280"/>
  <text x="370" y="250" text-anchor="middle" fill="#9ca3af" font-size="12" font-family="Inter,sans-serif" font-weight="500">Time</text>
  <line x1="130" y1="205" x2="130" y2="215" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="130" y="230" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 1</text>
  <line x1="370" y1="205" x2="370" y2="215" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="370" y="230" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 2</text>
  <line x1="580" y1="205" x2="580" y2="215" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="580" y="230" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 3</text>
</svg>

This means a revision that modifies a single record only writes the modified page plus its ancestor path — typically 3-4 pages. A 10 GB database with 1,000 revisions and 0.1% change each requires roughly 20 GB total, not 10 TB.

Physically, each resource is stored in two append-only logical devices (files). **LD₁** stores page content (IndirectPages, RecordPages, NamePages) followed by a RevisionRootPage at the end of each revision's data. **LD₂** stores the UberPage — a sequence of timestamp + offset pairs, one per revision, pointing to the corresponding RRP in LD₁.

<img src="/images/sirix-on-device-layout.svg" alt="Logical Device Layout: LD₂ stores UberPage with timestamp and offset pairs pointing to each revision's RevisionRootPage in LD₁. Each revision appends only modified page fragments (copy-on-write)." style="width:100%;max-width:960px;">

The `UberPage` is always written last as an atomic operation. Even if a crash occurs mid-commit, the previous valid state is preserved.

## Page Structure

Each resource is organized as a trie of pages. The `RevisionRootPage` is the entry point for a single revision, branching into subtrees for data, indexes, and metadata.

<svg viewBox="0 0 860 255" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:860px;" role="img" aria-label="Page hierarchy: RevisionRootPage branching into data and index subtrees, with UberPage as logical header">
  <text x="430" y="18" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Page Hierarchy (single revision)</text>

  <!-- UberPage (logical header) -->
  <rect x="390" y="32" width="80" height="28" rx="5" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="430" y="50" text-anchor="middle" fill="#42B6F0" font-size="10" font-family="JetBrains Mono,monospace" font-weight="600">UberPage</text>
  <line x1="430" y1="60" x2="430" y2="70" stroke="#42B6F0" stroke-width="1.2"/>

  <!-- RevisionRootPage (metadata inside box so lines don't cross it) -->
  <rect x="345" y="70" width="170" height="44" rx="5" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="430" y="89" text-anchor="middle" fill="#F47B20" font-size="10" font-family="JetBrains Mono,monospace" font-weight="600">RevisionRootPage</text>
  <text x="430" y="105" text-anchor="middle" fill="#6b7280" font-size="7" font-family="Inter,sans-serif">author, timestamp, commit message</text>

  <!-- Branches from RevisionRootPage (y=114) -->

  <!-- Data IndirectPages branch -->
  <line x1="365" y1="114" x2="90" y2="150" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="32" y="150" width="116" height="24" rx="4" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="90" y="166" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Data IndirectPages</text>
  <line x1="70" y1="174" x2="52" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="110" y1="174" x2="128" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="22" y="198" width="60" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="52" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">RecordPage</text>
  <rect x="98" y="198" width="60" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="128" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">RecordPage</text>
  <text x="90" y="236" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">JSON/XML nodes</text>

  <!-- PathSummary branch -->
  <line x1="390" y1="114" x2="245" y2="150" stroke="#F47B20" stroke-width="1"/>
  <rect x="197" y="150" width="96" height="24" rx="4" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="245" y="166" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">PathSummary</text>
  <text x="245" y="190" text-anchor="middle" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">unique path tree</text>

  <!-- NamePage branch -->
  <line x1="415" y1="114" x2="400" y2="150" stroke="#F47B20" stroke-width="1"/>
  <rect x="358" y="150" width="84" height="24" rx="4" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="400" y="166" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">NamePage</text>
  <line x1="385" y1="174" x2="364" y2="198" stroke="#F47B20" stroke-width="0.8"/>
  <line x1="415" y1="174" x2="436" y2="198" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="330" y="198" width="68" height="20" rx="3" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.8"/>
  <text x="364" y="212" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Index Tree 1</text>
  <rect x="402" y="198" width="68" height="20" rx="3" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.8"/>
  <text x="436" y="212" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Index Tree n</text>
  <text x="400" y="236" text-anchor="middle" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">name indexes</text>

  <!-- PathPage branch -->
  <line x1="455" y1="114" x2="580" y2="150" stroke="#42B6F0" stroke-width="1"/>
  <rect x="538" y="150" width="84" height="24" rx="4" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="580" y="166" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">PathPage</text>
  <line x1="565" y1="174" x2="544" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="595" y1="174" x2="616" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="510" y="198" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="544" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree 1</text>
  <rect x="582" y="198" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="616" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree n</text>
  <text x="580" y="236" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">path indexes</text>

  <!-- CASPage branch -->
  <line x1="485" y1="114" x2="755" y2="150" stroke="#42B6F0" stroke-width="1"/>
  <rect x="713" y="150" width="84" height="24" rx="4" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="755" y="166" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">CASPage</text>
  <line x1="740" y1="174" x2="719" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="770" y1="174" x2="791" y2="198" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="685" y="198" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="719" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree 1</text>
  <rect x="757" y="198" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="791" y="212" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree n</text>
  <text x="755" y="236" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">CAS indexes</text>
</svg>

**UberPage** — The root entry point. Written last during a commit as an atomic operation. Contains a reference to the IndirectPage tree that addresses all revisions.

**IndirectPages** — Fan-out nodes (512 references each) that form the trie structure. Borrowed from ZFS, they store checksums in parent references for data integrity. Unused slots are tracked with a bitset for compact storage.

**RevisionRootPage** — Entry point for a single revision. Stores the author, timestamp, and optional commit message. Branches to the data trie, path summary, name dictionary, and index pages.

**RecordPages** — Leaf pages storing up to 1024 nodes each. These are the pages that get versioned by the sliding snapshot algorithm.

## Sliding Snapshot Versioning

SirixDB doesn't just copy entire pages on every change. It versions `RecordPages` at a sub-page level, storing only changed records. The **sliding snapshot** algorithm, developed by Marc Kramis, avoids the trade-off between read performance and write amplification that plagues traditional approaches.

<svg viewBox="0 0 720 290" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Three versioning strategies compared: Full, Incremental, and Sliding Snapshot">
  <text x="360" y="18" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Page Versioning Strategies</text>

  <!-- Column headers -->
  <text x="120" y="42" text-anchor="middle" fill="#42B6F0" font-size="11" font-family="Inter,sans-serif" font-weight="600">Full Copy</text>
  <text x="360" y="42" text-anchor="middle" fill="#F47B20" font-size="11" font-family="Inter,sans-serif" font-weight="600">Incremental</text>
  <text x="600" y="42" text-anchor="middle" fill="#10b981" font-size="11" font-family="Inter,sans-serif" font-weight="600">Sliding Snapshot</text>

  <!-- Separators -->
  <line x1="240" y1="30" x2="240" y2="260" stroke="#6b7280" stroke-width="0.5" opacity="0.3"/>
  <line x1="480" y1="30" x2="480" y2="260" stroke="#6b7280" stroke-width="0.5" opacity="0.3"/>

  <!-- Rev labels -->
  <text x="20" y="78" fill="#6b7280" font-size="9" font-family="JetBrains Mono,monospace">Rev 1</text>
  <text x="20" y="118" fill="#6b7280" font-size="9" font-family="JetBrains Mono,monospace">Rev 2</text>
  <text x="20" y="158" fill="#6b7280" font-size="9" font-family="JetBrains Mono,monospace">Rev 3</text>
  <text x="20" y="198" fill="#6b7280" font-size="9" font-family="JetBrains Mono,monospace">Rev 4</text>
  <text x="20" y="238" fill="#6b7280" font-size="9" font-family="JetBrains Mono,monospace">Rev 5</text>

  <!-- FULL COPY column -->
  <!-- Rev 1: full page [A B C D] -->
  <rect x="68" y="62" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="120" y="77" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">A  B  C  D</text>
  <!-- Rev 2: full page [A B' C D] -->
  <rect x="68" y="102" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="120" y="117" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">A  <tspan fill="#F47B20">B'</tspan> C  D</text>
  <!-- Rev 3 -->
  <rect x="68" y="142" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="120" y="157" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">A  B' <tspan fill="#F47B20">C'</tspan> D</text>
  <!-- Rev 4 -->
  <rect x="68" y="182" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="120" y="197" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace"><tspan fill="#F47B20">A'</tspan> B' C' D</text>
  <!-- Rev 5 -->
  <rect x="68" y="222" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="120" y="237" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">A' B' C' <tspan fill="#F47B20">D'</tspan></text>

  <text x="120" y="265" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Fast reads, wasteful writes</text>

  <!-- INCREMENTAL column -->
  <!-- Rev 1: full dump -->
  <rect x="308" y="62" width="104" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1"/>
  <text x="360" y="77" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">A  B  C  D</text>
  <!-- Rev 2: only delta -->
  <rect x="338" y="102" width="44" height="22" rx="3" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1"/>
  <text x="360" y="117" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">B'</text>
  <!-- Rev 3: only delta -->
  <rect x="338" y="142" width="44" height="22" rx="3" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1"/>
  <text x="360" y="157" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">C'</text>
  <!-- Rev 4: full dump again (write spike!) -->
  <rect x="308" y="182" width="104" height="22" rx="3" fill="rgba(244,123,32,0.3)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="360" y="197" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">A' B' C' D</text>
  <text x="425" y="197" fill="#F47B20" font-size="7" font-family="Inter,sans-serif" font-style="italic">write spike!</text>
  <!-- Rev 5: delta -->
  <rect x="338" y="222" width="44" height="22" rx="3" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1"/>
  <text x="360" y="237" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">D'</text>

  <text x="360" y="265" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Compact, but periodic write spikes</text>

  <!-- SLIDING SNAPSHOT column (window N=3) -->
  <!-- Rev 1: full -->
  <rect x="548" y="62" width="104" height="22" rx="3" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1"/>
  <text x="600" y="77" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">A  B  C  D</text>
  <!-- Rev 2: changed + window carry -->
  <rect x="558" y="102" width="84" height="22" rx="3" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1"/>
  <text x="600" y="117" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">B'</text>
  <!-- Rev 3 -->
  <rect x="558" y="142" width="84" height="22" rx="3" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1"/>
  <text x="600" y="157" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">C' <tspan fill="#9ca3af" font-size="7">+ A,D</tspan></text>
  <!-- Rev 4: changed + expired from window -->
  <rect x="558" y="182" width="84" height="22" rx="3" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1"/>
  <text x="600" y="197" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">A' <tspan fill="#9ca3af" font-size="7">+ B',C'</tspan></text>
  <!-- Rev 5 -->
  <rect x="558" y="222" width="84" height="22" rx="3" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1"/>
  <text x="600" y="237" text-anchor="middle" fill="#10b981" font-size="8" font-family="JetBrains Mono,monospace">D' <tspan fill="#9ca3af" font-size="7">+ A'</tspan></text>

  <text x="600" y="265" text-anchor="middle" fill="#10b981" font-size="8" font-family="Inter,sans-serif" font-weight="500">Bounded reads, no spikes</text>
</svg>

| Strategy | Reads to reconstruct | Write cost per revision | Write spikes? |
|----------|---------------------|------------------------|---------------|
| **Full** | 1 page | Entire page (all records) | No |
| **Incremental** | Up to all revisions | Only changed records | Yes (periodic full dump) |
| **Differential** | 2 pages | All changes since last full dump | Yes (growing deltas) |
| **Sliding Snapshot** | At most N fragments | Changed + expired records | **No** |

The sliding snapshot uses a window of size N (typically 3-5). Changed records are always written. Records older than N revisions that haven't been written are carried forward. This guarantees that at most N page fragments need to be read to reconstruct any page — regardless of total revision count.

For details, see Marc Kramis's thesis: [Evolutionary Tree-Structured Storage: Concepts, Interfaces, and Applications](http://kops.uni-konstanz.de/handle/123456789/27695).

## Secondary Indexes

SirixDB supports three types of user-defined secondary indexes, all stored in the same versioned trie structure as the data. Indexes are part of the transaction and version with the data — the index at revision 42 always matches the data at revision 42.

### Path Summary

Every resource maintains a compact **path summary** — a tree of all unique paths in the document. Each unique path gets a **path class reference (PCR)**, a stable integer ID. Nodes in the main data tree reference their PCR, enabling efficient path-based lookups.

<svg viewBox="0 0 720 380" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Path Summary maps unique paths to path class references, connecting data tree nodes to index entries">
  <text x="360" y="16" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Path Summary and Index Architecture</text>

  <!-- === Left side: JSON Data Tree === -->
  <text x="160" y="36" text-anchor="middle" fill="#42B6F0" font-size="11" font-family="Inter,sans-serif" font-weight="600">Data Tree</text>

  <!-- DocumentRootNode (virtual) — dashed border -->
  <rect x="95" y="44" width="130" height="20" rx="3" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="160" y="58" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">DocumentRootNode</text>
  <line x1="160" y1="64" x2="160" y2="75" stroke="#42B6F0" stroke-width="0.8"/>

  <!-- Root object -->
  <rect x="130" y="77" width="60" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="160" y="92" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">OBJECT</text>

  <!-- "users" key -->
  <line x1="160" y1="99" x2="100" y2="117" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="62" y="119" width="76" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="100" y="133" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">KEY "users"</text>

  <!-- "config" key -->
  <line x1="160" y1="99" x2="220" y2="117" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="182" y="119" width="76" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="220" y="133" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">KEY "config"</text>

  <!-- Array under users -->
  <line x1="100" y1="139" x2="100" y2="154" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="74" y="156" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="100" y="169" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">ARRAY</text>

  <!-- User objects -->
  <line x1="85" y1="174" x2="50" y2="192" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="115" y1="174" x2="150" y2="192" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="24" y="192" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="50" y="205" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">OBJ</text>
  <rect x="124" y="192" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="150" y="205" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">OBJ</text>

  <!-- Left OBJ fields: "name" and "age" -->
  <line x1="38" y1="210" x2="30" y2="226" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="10" y="226" width="40" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="30" y="237" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"name"</text>
  <line x1="30" y1="242" x2="30" y2="256" stroke="#10b981" stroke-width="0.6"/>
  <rect x="6" y="256" width="48" height="14" rx="2" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="0.6"/>
  <text x="30" y="266" text-anchor="middle" fill="#10b981" font-size="6" font-family="JetBrains Mono,monospace">"Alice"</text>

  <line x1="62" y1="210" x2="70" y2="226" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="52" y="226" width="36" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="70" y="237" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"age"</text>
  <line x1="70" y1="242" x2="70" y2="256" stroke="#10b981" stroke-width="0.6"/>
  <rect x="56" y="256" width="28" height="14" rx="2" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="0.6"/>
  <text x="70" y="266" text-anchor="middle" fill="#10b981" font-size="6" font-family="JetBrains Mono,monospace">28</text>

  <!-- Right OBJ fields: "name" and "age" -->
  <line x1="138" y1="210" x2="130" y2="226" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="110" y="226" width="40" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="130" y="237" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"name"</text>
  <line x1="130" y1="242" x2="130" y2="256" stroke="#10b981" stroke-width="0.6"/>
  <rect x="108" y="256" width="44" height="14" rx="2" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="0.6"/>
  <text x="130" y="266" text-anchor="middle" fill="#10b981" font-size="6" font-family="JetBrains Mono,monospace">"Bob"</text>

  <line x1="162" y1="210" x2="170" y2="226" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="152" y="226" width="36" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="170" y="237" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"age"</text>
  <line x1="170" y1="242" x2="170" y2="256" stroke="#10b981" stroke-width="0.6"/>
  <rect x="158" y="256" width="24" height="14" rx="2" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="0.6"/>
  <text x="170" y="266" text-anchor="middle" fill="#10b981" font-size="6" font-family="JetBrains Mono,monospace">35</text>

  <!-- === Right side: Path Summary === -->
  <text x="540" y="36" text-anchor="middle" fill="#F47B20" font-size="11" font-family="Inter,sans-serif" font-weight="600">Path Summary</text>

  <!-- DocumentRootNode (virtual) — dashed border -->
  <rect x="475" y="44" width="130" height="20" rx="3" fill="rgba(244,123,32,0.1)" stroke="#F47B20" stroke-width="1.2" stroke-dasharray="4 2"/>
  <text x="540" y="58" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">DocumentRootNode</text>
  <text x="615" y="58" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=0</text>

  <!-- /users -->
  <line x1="518" y1="64" x2="470" y2="117" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="434" y="119" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="470" y="133" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">users</text>
  <text x="516" y="133" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=1</text>

  <!-- /config -->
  <line x1="562" y1="64" x2="590" y2="117" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="554" y="119" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="590" y="133" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">config</text>
  <text x="636" y="133" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=5</text>

  <!-- /users/[] -->
  <line x1="470" y1="139" x2="470" y2="154" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="440" y="156" width="60" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="470" y="170" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">[]</text>
  <text x="510" y="170" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=2</text>

  <!-- /users/[]/name -->
  <line x1="458" y1="176" x2="420" y2="224" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="384" y="226" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="420" y="240" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">name</text>
  <text x="420" y="254" text-anchor="middle" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=3</text>

  <!-- /users/[]/age -->
  <line x1="482" y1="176" x2="520" y2="224" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="484" y="226" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="520" y="240" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">age</text>
  <text x="566" y="240" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=4</text>

  <!-- PCR dashed connections from data tree to path summary -->
  <!-- DocumentRootNode → DocumentRootNode -->
  <line x1="225" y1="54" x2="475" y2="54" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4"/>
  <!-- KEY "users" → users -->
  <path d="M 138,129 Q 286,97 434,129" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4" fill="none"/>
  <!-- KEY "config" → config -->
  <path d="M 258,129 Q 406,167 554,129" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4" fill="none"/>
  <!-- ARRAY → [] -->
  <line x1="126" y1="165" x2="440" y2="165" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4"/>
  <!-- Left "name" → name (gentle arc above keys) -->
  <path d="M 30,226 Q 210,208 384,236" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4" fill="none"/>
  <!-- Right "name" → name (gentle arc above keys) -->
  <path d="M 130,226 Q 260,210 384,236" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4" fill="none"/>
  <!-- Left "age" → age (higher arc, bypasses PS name box) -->
  <path d="M 70,226 C 280,186 484,210 484,236" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="4 3" opacity="0.35" fill="none"/>
  <!-- Right "age" → age (higher arc, bypasses PS name box) -->
  <path d="M 170,226 C 330,190 484,210 484,236" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="4 3" opacity="0.35" fill="none"/>

  <!-- Index section below -->
  <line x1="40" y1="278" x2="680" y2="278" stroke="#6b7280" stroke-width="0.5" opacity="0.3"/>
  <text x="360" y="300" text-anchor="middle" fill="#e8e6e3" font-size="11" font-family="Inter,sans-serif" font-weight="600">Index Types</text>

  <!-- Name Index -->
  <rect x="40" y="314" width="190" height="38" rx="5" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="1"/>
  <text x="135" y="328" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="Inter,sans-serif" font-weight="600">Name Index</text>
  <text x="135" y="344" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">hash("name") → {key5,key12}</text>

  <!-- Path Index -->
  <rect x="260" y="314" width="200" height="38" rx="5" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="1"/>
  <text x="360" y="328" text-anchor="middle" fill="#F47B20" font-size="9" font-family="Inter,sans-serif" font-weight="600">Path Index</text>
  <text x="360" y="344" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">PCR=3 → {key5, key12}</text>

  <!-- CAS Index -->
  <rect x="490" y="314" width="200" height="38" rx="5" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="1"/>
  <text x="590" y="328" text-anchor="middle" fill="#10b981" font-size="9" font-family="Inter,sans-serif" font-weight="600">CAS Index</text>
  <text x="590" y="344" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">(PCR=4, 30) → {key7}</text>
</svg>

### Index Types

| Index | Key | Use case |
|-------|-----|----------|
| **Name** | Field name hash → node keys | Find all nodes named `"email"` regardless of path |
| **Path** | PCR → node keys | Find all nodes at path `/users/[]/name` |
| **CAS** | (PCR + typed value) → node keys | Find all users where `age > 30` on path `/users/[]/age` |

CAS (content-and-structure) indexes are the most selective — they index both the path and the typed value, enabling efficient range queries. All indexes are stored in Height Optimized Tries (HOT) within the same versioned page structure.

For the JSONiq API to create and query indexes, see the [Function Reference](/docs/jsoniq-functions.html#indexes).

## Further Reading

- [Evolutionary Tree-Structured Storage](http://kops.uni-konstanz.de/handle/123456789/27695) — Marc Kramis's thesis describing the sliding snapshot algorithm
- [SirixDB on GitHub](https://github.com/sirixdb/sirix) — source code and detailed `docs/ARCHITECTURE.md`
- [REST API documentation](/docs/rest-api.html) — HTTP interface for SirixDB
- [JSONiq API](/docs/jsoniq-api.html) — query language guide
