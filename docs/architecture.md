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

  <!-- Sibling arrow between array items -->
  <line x1="485" y1="275" x2="515" y2="275" stroke="#9ca3af" stroke-width="0.8" stroke-dasharray="3 2" marker-end="url(#arrowGray)"/>
  <defs><marker id="arrowGray" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto"><path d="M0,0 L6,2 L0,4" fill="#9ca3af"/></marker></defs>

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

<svg viewBox="0 0 720 330" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Copy-on-write: modifying a leaf copies only the path to root, sharing unchanged pages">
  <!-- Legend -->
  <rect x="20" y="8" width="12" height="12" rx="2" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="38" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">New / copied page</text>
  <rect x="170" y="8" width="12" height="12" rx="2" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="188" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">Modified page</text>
  <line x1="320" y1="14" x2="360" y2="14" stroke="#6b7280" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>
  <text x="368" y="18" fill="#9ca3af" font-size="10" font-family="Inter,sans-serif">Shared pointer (unchanged)</text>

  <!-- Timeline -->
  <line x1="60" y1="285" x2="680" y2="285" stroke="#6b7280" stroke-width="1.5"/>
  <polygon points="680,285 670,280 670,290" fill="#6b7280"/>
  <text x="370" y="320" text-anchor="middle" fill="#9ca3af" font-size="12" font-family="Inter,sans-serif" font-weight="500">Time</text>

  <!-- Rev labels -->
  <line x1="130" y1="280" x2="130" y2="290" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="130" y="305" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 1</text>
  <line x1="370" y1="280" x2="370" y2="290" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="370" y="305" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 2</text>
  <line x1="580" y1="280" x2="580" y2="290" stroke="#9ca3af" stroke-width="1.5"/>
  <text x="580" y="305" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="JetBrains Mono,monospace" font-weight="500">Rev 3</text>

  <!-- === Rev 1 === -->
  <!-- UberPage -->
  <rect x="104" y="40" width="52" height="24" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="130" y="56" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <!-- IndirectPage -->
  <line x1="130" y1="64" x2="130" y2="90" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="100" y="92" width="60" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="130" y="107" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">Indirect</text>
  <!-- RevRootPage -->
  <line x1="130" y1="114" x2="130" y2="135" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="97" y="137" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="130" y="152" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Data indirect -->
  <line x1="115" y1="159" x2="80" y2="178" stroke="#42B6F0" stroke-width="1"/>
  <line x1="145" y1="159" x2="180" y2="178" stroke="#42B6F0" stroke-width="1"/>
  <rect x="52" y="180" width="56" height="20" rx="3" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="80" y="194" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Indirect</text>
  <rect x="152" y="180" width="56" height="20" rx="3" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="180" y="194" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Indirect</text>
  <!-- RecordPages -->
  <line x1="66" y1="200" x2="58" y2="218" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="94" y1="200" x2="102" y2="218" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="38" y="220" width="40" height="18" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="58" y="232" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page A</text>
  <rect x="82" y="220" width="40" height="18" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="102" y="232" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page B</text>
  <line x1="166" y1="200" x2="158" y2="218" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="194" y1="200" x2="202" y2="218" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="138" y="220" width="40" height="18" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="158" y="232" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page C</text>
  <rect x="182" y="220" width="40" height="18" rx="2" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="202" y="232" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">Page D</text>

  <!-- === Rev 2: modify Page A, copy path === -->
  <rect x="344" y="40" width="52" height="24" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="370" y="56" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <line x1="370" y1="64" x2="370" y2="90" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="340" y="92" width="60" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="370" y="107" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">Indirect</text>
  <line x1="370" y1="114" x2="370" y2="135" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="337" y="137" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="370" y="152" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Left branch: copied (modified) -->
  <line x1="355" y1="159" x2="330" y2="178" stroke="#F47B20" stroke-width="1.2"/>
  <rect x="302" y="180" width="56" height="20" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="330" y="194" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Indirect'</text>
  <!-- Modified Page A' -->
  <line x1="316" y1="200" x2="306" y2="218" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="286" y="220" width="40" height="18" rx="2" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="306" y="232" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">Page A'</text>
  <!-- Shared pointer to Page B -->
  <line x1="344" y1="200" x2="102" y2="229" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Right branch: shared pointer to Rev1's right indirect -->
  <line x1="385" y1="159" x2="180" y2="190" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>

  <!-- === Rev 3: modify Page D, share rest === -->
  <rect x="554" y="40" width="52" height="24" rx="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="580" y="56" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">Uber</text>
  <line x1="580" y1="64" x2="580" y2="90" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="550" y="92" width="60" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="580" y="107" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">Indirect</text>
  <line x1="580" y1="114" x2="580" y2="135" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="547" y="137" width="66" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="580" y="152" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">RevRoot</text>
  <!-- Left: share Rev2's left indirect (which includes Page A') -->
  <line x1="565" y1="159" x2="330" y2="190" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Right: modified -->
  <line x1="595" y1="159" x2="620" y2="178" stroke="#F47B20" stroke-width="1.2"/>
  <rect x="592" y="180" width="56" height="20" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="620" y="194" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">Indirect'</text>
  <!-- Shared Page C -->
  <line x1="606" y1="200" x2="158" y2="229" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
  <!-- Modified Page D' -->
  <line x1="634" y1="200" x2="644" y2="218" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="624" y="220" width="40" height="18" rx="2" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="644" y="232" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">Page D'</text>

  <!-- Annotations -->
  <text x="306" y="258" text-anchor="middle" fill="#F47B20" font-size="8" font-family="Inter,sans-serif" font-style="italic">only changed path copied</text>
</svg>

This means a revision that modifies a single record only writes the modified page plus its ancestor path — typically 3-4 pages. A 10 GB database with 1,000 revisions and 0.1% change each requires roughly 20 GB total, not 10 TB.

The `UberPage` is always written last as an atomic operation. Even if a crash occurs mid-commit, the previous valid state is preserved.

## Page Structure

Each resource is organized as a trie of pages. The `RevisionRootPage` is the entry point for a single revision, branching into subtrees for data, indexes, and metadata.

<svg viewBox="0 0 720 310" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Page hierarchy: UberPage to RevisionRootPage to data and index subtrees">
  <text x="360" y="18" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Page Hierarchy (single revision)</text>

  <!-- UberPage -->
  <rect x="320" y="32" width="80" height="28" rx="5" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="360" y="50" text-anchor="middle" fill="#42B6F0" font-size="10" font-family="JetBrains Mono,monospace" font-weight="600">UberPage</text>

  <!-- IndirectPage (to revisions) -->
  <line x1="360" y1="60" x2="360" y2="78" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="310" y="80" width="100" height="24" rx="4" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="360" y="96" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">IndirectPages</text>

  <!-- RevisionRootPage -->
  <line x1="360" y1="104" x2="360" y2="122" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="290" y="124" width="140" height="28" rx="5" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="360" y="142" text-anchor="middle" fill="#F47B20" font-size="10" font-family="JetBrains Mono,monospace" font-weight="600">RevisionRootPage</text>
  <text x="360" y="168" text-anchor="middle" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">author, timestamp, commit message</text>

  <!-- Branches from RevisionRootPage -->
  <!-- Data branch (center-left) -->
  <line x1="310" y1="152" x2="120" y2="195" stroke="#42B6F0" stroke-width="1.2"/>
  <rect x="62" y="197" width="116" height="24" rx="4" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="120" y="213" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Data IndirectPages</text>
  <line x1="98" y1="221" x2="72" y2="242" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="142" y1="221" x2="168" y2="242" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="42" y="244" width="60" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="72" y="258" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">RecordPage</text>
  <rect x="138" y="244" width="60" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="168" y="258" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">RecordPage</text>
  <text x="120" y="282" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">JSON/XML nodes</text>

  <!-- PathSummary branch -->
  <line x1="335" y1="152" x2="300" y2="195" stroke="#F47B20" stroke-width="1"/>
  <rect x="252" y="197" width="96" height="24" rx="4" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="300" y="213" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">PathSummary</text>
  <text x="300" y="237" text-anchor="middle" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">unique path trie</text>

  <!-- NamePage branch -->
  <line x1="385" y1="152" x2="440" y2="195" stroke="#F47B20" stroke-width="1"/>
  <rect x="398" y="197" width="84" height="24" rx="4" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="440" y="213" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">NamePage</text>
  <text x="440" y="237" text-anchor="middle" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">field name dictionary</text>

  <!-- Index branches (PathPage + CASPage) -->
  <line x1="410" y1="152" x2="600" y2="195" stroke="#42B6F0" stroke-width="1"/>
  <rect x="548" y="197" width="104" height="24" rx="4" fill="rgba(66,182,240,0.15)" stroke="#42B6F0" stroke-width="1"/>
  <text x="600" y="213" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">PathPage / CASPage</text>
  <line x1="580" y1="221" x2="564" y2="242" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="620" y1="221" x2="636" y2="242" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="530" y="244" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="564" y="258" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree 1</text>
  <rect x="602" y="244" width="68" height="20" rx="3" fill="rgba(66,182,240,0.1)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="636" y="258" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">Index Tree 2</text>
  <text x="600" y="282" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">user-defined indexes</text>
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

Every resource maintains a compact **path summary** — a trie of all unique paths in the document. Each unique path gets a **path class reference (PCR)**, a stable integer ID. Nodes in the main data tree reference their PCR, enabling efficient path-based lookups.

<svg viewBox="0 0 720 340" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;" role="img" aria-label="Path Summary maps unique paths to path class references, connecting data tree nodes to index entries">
  <text x="360" y="18" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Path Summary and Index Architecture</text>

  <!-- Left side: JSON Data Tree -->
  <text x="160" y="44" text-anchor="middle" fill="#42B6F0" font-size="11" font-family="Inter,sans-serif" font-weight="600">Data Tree</text>

  <!-- Root object -->
  <rect x="130" y="55" width="60" height="22" rx="3" fill="rgba(66,182,240,0.2)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="160" y="70" text-anchor="middle" fill="#42B6F0" font-size="8" font-family="JetBrains Mono,monospace">OBJECT</text>

  <!-- "users" key -->
  <line x1="160" y1="77" x2="100" y2="95" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="62" y="97" width="76" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="100" y="111" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">KEY "users"</text>

  <!-- "config" key -->
  <line x1="160" y1="77" x2="220" y2="95" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="182" y="97" width="76" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="220" y="111" text-anchor="middle" fill="#F47B20" font-size="7" font-family="JetBrains Mono,monospace">KEY "config"</text>

  <!-- Array under users -->
  <line x1="100" y1="117" x2="100" y2="132" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="74" y="134" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="100" y="147" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">ARRAY</text>

  <!-- User objects -->
  <line x1="88" y1="152" x2="60" y2="168" stroke="#42B6F0" stroke-width="0.8"/>
  <line x1="112" y1="152" x2="140" y2="168" stroke="#42B6F0" stroke-width="0.8"/>
  <rect x="34" y="170" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="60" y="183" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">OBJ</text>
  <rect x="114" y="170" width="52" height="18" rx="3" fill="rgba(66,182,240,0.12)" stroke="#42B6F0" stroke-width="0.8"/>
  <text x="140" y="183" text-anchor="middle" fill="#42B6F0" font-size="7" font-family="JetBrains Mono,monospace">OBJ</text>

  <!-- name fields -->
  <line x1="48" y1="188" x2="48" y2="202" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="22" y="204" width="52" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="48" y="215" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"name"</text>
  <line x1="72" y1="188" x2="72" y2="202" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="60" y="224" width="42" height="14" rx="2" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="0.6"/>
  <text x="81" y="234" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">"Alice"</text>

  <line x1="128" y1="188" x2="128" y2="202" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="102" y="204" width="52" height="16" rx="2" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="0.6"/>
  <text x="128" y="215" text-anchor="middle" fill="#F47B20" font-size="6" font-family="JetBrains Mono,monospace">"name"</text>
  <line x1="152" y1="188" x2="152" y2="202" stroke="#F47B20" stroke-width="0.6"/>
  <rect x="140" y="224" width="42" height="14" rx="2" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="0.6"/>
  <text x="161" y="234" text-anchor="middle" fill="#42B6F0" font-size="6" font-family="JetBrains Mono,monospace">"Bob"</text>

  <!-- Right side: Path Summary -->
  <text x="520" y="44" text-anchor="middle" fill="#F47B20" font-size="11" font-family="Inter,sans-serif" font-weight="600">Path Summary</text>

  <!-- Root path -->
  <rect x="494" y="55" width="52" height="22" rx="3" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="520" y="70" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">/</text>
  <text x="556" y="70" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=0</text>

  <!-- /users -->
  <line x1="508" y1="77" x2="470" y2="95" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="434" y="97" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="470" y="111" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">users</text>
  <text x="516" y="111" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=1</text>

  <!-- /config -->
  <line x1="532" y1="77" x2="590" y2="95" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="554" y="97" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="590" y="111" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">config</text>
  <text x="636" y="111" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=5</text>

  <!-- /users/[] -->
  <line x1="470" y1="117" x2="470" y2="132" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="440" y="134" width="60" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="470" y="148" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">[]</text>
  <text x="510" y="148" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=2</text>

  <!-- /users/[]/name -->
  <line x1="458" y1="154" x2="440" y2="170" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="404" y="172" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="440" y="186" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">name</text>
  <text x="486" y="186" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=3</text>

  <!-- /users/[]/age -->
  <line x1="482" y1="154" x2="540" y2="170" stroke="#F47B20" stroke-width="0.8"/>
  <rect x="504" y="172" width="72" height="20" rx="3" fill="rgba(244,123,32,0.12)" stroke="#F47B20" stroke-width="1"/>
  <text x="540" y="186" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace">age</text>
  <text x="586" y="186" fill="#6b7280" font-size="7" font-family="JetBrains Mono,monospace">PCR=4</text>

  <!-- PCR arrows from data to path summary -->
  <line x1="138" y1="100" x2="434" y2="100" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4"/>
  <line x1="154" y1="210" x2="404" y2="183" stroke="#9ca3af" stroke-width="0.6" stroke-dasharray="3 2" opacity="0.4"/>

  <!-- Index section below -->
  <line x1="40" y1="256" x2="680" y2="256" stroke="#6b7280" stroke-width="0.5" opacity="0.3"/>
  <text x="360" y="278" text-anchor="middle" fill="#e8e6e3" font-size="11" font-family="Inter,sans-serif" font-weight="600">Index Types</text>

  <!-- Name Index -->
  <rect x="40" y="292" width="190" height="38" rx="5" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="1"/>
  <text x="135" y="306" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="Inter,sans-serif" font-weight="600">Name Index</text>
  <text x="135" y="322" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">hash("name") → {key5,key12}</text>

  <!-- Path Index -->
  <rect x="260" y="292" width="200" height="38" rx="5" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="1"/>
  <text x="360" y="306" text-anchor="middle" fill="#F47B20" font-size="9" font-family="Inter,sans-serif" font-weight="600">Path Index</text>
  <text x="360" y="322" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">PCR=3 → {key5, key12}</text>

  <!-- CAS Index -->
  <rect x="490" y="292" width="200" height="38" rx="5" fill="rgba(16,185,129,0.08)" stroke="#10b981" stroke-width="1"/>
  <text x="590" y="306" text-anchor="middle" fill="#10b981" font-size="9" font-family="Inter,sans-serif" font-weight="600">CAS Index</text>
  <text x="590" y="322" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="JetBrains Mono,monospace">(PCR=4, 30) → {key7}</text>
</svg>

### Index Types

| Index | Key | Use case |
|-------|-----|----------|
| **Name** | Field name hash → node keys | Find all nodes named `"email"` regardless of path |
| **Path** | PCR → node keys | Find all nodes at path `/users/[]/name` |
| **CAS** | (PCR + typed value) → node keys | Find all users where `age > 30` on path `/users/[]/age` |

CAS (content-and-structure) indexes are the most selective — they index both the path and the typed value, enabling efficient range queries. All indexes are stored in balanced binary search trees (Red-Black trees) within the same versioned page structure.

For the JSONiq API to create and query indexes, see the [Function Reference](/docs/jsoniq-functions.html#indexes).

## Further Reading

- [Evolutionary Tree-Structured Storage](http://kops.uni-konstanz.de/handle/123456789/27695) — Marc Kramis's thesis describing the sliding snapshot algorithm
- [SirixDB on GitHub](https://github.com/sirixdb/sirix) — source code and detailed `docs/ARCHITECTURE.md`
- [REST API documentation](/docs/rest-api.html) — HTTP interface for SirixDB
- [JSONiq API](/docs/jsoniq-api.html) — query language guide
