---
layout: documentation
doctitle: Use Cases
title: SirixDB - Real-World Use Cases for Bitemporal Data
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/use-cases.md)

## Why Bitemporality Matters

Most databases track one version of the truth: the current state. When you update a row, the old value is gone. Some databases add a single timeline (system versioning), but real-world data has **two independent timelines**:

- **Transaction time**: When was this fact recorded in the database?
- **Valid time**: When was this fact true in the real world?

These two timelines diverge constantly. A price correction recorded today might apply retroactively to last month. A medical diagnosis entered on Tuesday might be backdated to the previous week. Without bitemporality, you are forced to choose which timeline to preserve — and the one you discard is inevitably the one someone needs.

SirixDB tracks both timelines natively. This makes an entire class of applications not just possible, but straightforward. Below are concrete use cases that are **difficult or impractical** to build on conventional databases, but become natural with SirixDB.

<svg viewBox="-70 0 930 280" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:1180px;" role="img" aria-label="Two timelines diverge: transaction time records when facts were stored, valid time records when they were true in the real world">
  <!-- Title -->
  <text x="430" y="24" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Two Timelines, One Reality</text>

  <!-- Transaction Time Timeline (Blue) -->
  <text x="88" y="78" text-anchor="end" fill="#42B6F0" font-size="11" font-family="Inter,sans-serif" font-weight="600">Transaction Time</text>
  <text x="88" y="93" text-anchor="end" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">(when recorded in the system)</text>
  <line x1="100" y1="85" x2="790" y2="85" stroke="#42B6F0" stroke-width="1.5" opacity="0.4"/>
  <polygon points="790,85 780,80 780,90" fill="#42B6F0" opacity="0.4"/>

  <!-- TX Event: Jan 5 -->
  <circle cx="200" cy="85" r="6" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="200" y="68" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">Jan 5</text>
  <text x="200" y="110" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Insert price $100</text>

  <!-- TX Event: Mar 15 -->
  <circle cx="520" cy="85" r="6" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="520" y="68" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">Mar 15</text>
  <text x="520" y="110" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Error discovered</text>

  <!-- TX Event: Mar 20 (orange accent — the correction) -->
  <circle cx="660" cy="85" r="7" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="2"/>
  <text x="660" y="68" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">Mar 20</text>
  <text x="660" y="110" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Correction recorded</text>

  <!-- Valid Time Timeline (Orange) -->
  <text x="88" y="208" text-anchor="end" fill="#F47B20" font-size="11" font-family="Inter,sans-serif" font-weight="600">Valid Time</text>
  <text x="88" y="223" text-anchor="end" fill="#6b7280" font-size="8" font-family="Inter,sans-serif">(when true in the real world)</text>
  <line x1="100" y1="215" x2="790" y2="215" stroke="#F47B20" stroke-width="1.5" opacity="0.4"/>
  <polygon points="790,215 780,210 780,220" fill="#F47B20" opacity="0.4"/>

  <!-- VT Event: Jan 5 -->
  <circle cx="200" cy="215" r="6" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="1.5"/>
  <text x="200" y="198" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">Jan 5</text>
  <text x="200" y="240" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Original: $100</text>

  <!-- VT Event: Feb 1 (correction applies retroactively here) -->
  <circle cx="340" cy="215" r="7" fill="rgba(244,123,32,0.2)" stroke="#F47B20" stroke-width="2"/>
  <text x="340" y="198" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace" font-weight="500">Feb 1</text>
  <text x="340" y="240" text-anchor="middle" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Corrected: $95</text>

  <!-- Dashed connector: bottom of Mar 20 circle → top of Feb 1 circle -->
  <line x1="660" y1="92" x2="340" y2="208" stroke="#F47B20" stroke-width="1.5" stroke-dasharray="6 4" opacity="0.6"/>

  <!-- Annotation (positioned right of the dashed line to avoid overlap) -->
  <rect x="570" y="133" width="260" height="26" rx="4" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="1" opacity="0.6"/>
  <text x="700" y="150" text-anchor="middle" fill="#F47B20" font-size="9" font-family="Inter,sans-serif" font-weight="500">Recorded Mar 20 — but true since Feb 1</text>
</svg>

---

## Financial Services & Regulatory Compliance

### Regulatory Audit Trails

Financial institutions must answer questions like: *"What did we know about this customer's risk exposure on March 1st, as understood on March 15th — versus after a correction was applied on March 20th?"*

With SirixDB, this is a single bitemporal query. Without it, teams build shadow audit tables, change-data-capture pipelines, and custom versioning layers — fragile infrastructure that is expensive to maintain and inevitably incomplete.

<svg viewBox="0 0 860 400" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:1180px;" role="img" aria-label="Bitemporal coordinate grid showing how a query selects a specific point in two-dimensional temporal space">
  <!-- Title -->
  <text x="430" y="24" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Bitemporal Coordinate Space</text>

  <!-- Y-axis: Transaction Time (bottom → top) -->
  <line x1="160" y1="345" x2="160" y2="50" stroke="#42B6F0" stroke-width="1.5" opacity="0.5"/>
  <polygon points="160,50 155,60 165,60" fill="#42B6F0" opacity="0.5"/>
  <text x="25" y="200" text-anchor="middle" fill="#42B6F0" font-size="11" font-family="Inter,sans-serif" font-weight="600" transform="rotate(-90,25,200)">Transaction Time</text>

  <!-- X-axis: Valid Time (left → right) -->
  <line x1="160" y1="345" x2="780" y2="345" stroke="#F47B20" stroke-width="1.5" opacity="0.5"/>
  <polygon points="780,345 770,340 770,350" fill="#F47B20" opacity="0.5"/>
  <text x="470" y="390" text-anchor="middle" fill="#F47B20" font-size="11" font-family="Inter,sans-serif" font-weight="600">Valid Time</text>

  <!-- Grid lines — vertical (Valid Time months) -->
  <line x1="260" y1="55" x2="260" y2="345" stroke="#374151" stroke-width="0.7"/>
  <line x1="400" y1="55" x2="400" y2="345" stroke="#374151" stroke-width="0.7"/>
  <line x1="540" y1="55" x2="540" y2="345" stroke="#374151" stroke-width="0.7"/>
  <line x1="680" y1="55" x2="680" y2="345" stroke="#374151" stroke-width="0.7"/>

  <!-- Grid lines — horizontal (Transaction Time months) -->
  <line x1="160" y1="105" x2="760" y2="105" stroke="#374151" stroke-width="0.7"/>
  <line x1="160" y1="175" x2="760" y2="175" stroke="#374151" stroke-width="0.7"/>
  <line x1="160" y1="245" x2="760" y2="245" stroke="#374151" stroke-width="0.7"/>
  <line x1="160" y1="315" x2="760" y2="315" stroke="#374151" stroke-width="0.7"/>

  <!-- X-axis labels (Valid Time months) -->
  <text x="260" y="365" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace">Jan</text>
  <text x="400" y="365" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace">Feb</text>
  <text x="540" y="365" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace">Mar</text>
  <text x="680" y="365" text-anchor="middle" fill="#F47B20" font-size="9" font-family="JetBrains Mono,monospace">Apr</text>

  <!-- Y-axis labels (Transaction Time months, bottom→top = Jan→Apr) -->
  <text x="145" y="318" text-anchor="end" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Jan</text>
  <text x="145" y="248" text-anchor="end" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Feb</text>
  <text x="145" y="178" text-anchor="end" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Mar</text>
  <text x="145" y="108" text-anchor="end" fill="#42B6F0" font-size="9" font-family="JetBrains Mono,monospace">Apr</text>

  <!-- Revision band: Rev 1 — Jan 5, initial data (blue) -->
  <rect x="161" y="300" width="598" height="28" rx="3" fill="rgba(66,182,240,0.06)"/>
  <circle cx="260" cy="314" r="4" fill="rgba(66,182,240,0.25)" stroke="#42B6F0" stroke-width="1.2"/>
  <text x="770" y="318" text-anchor="start" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Rev 1: Initial data</text>

  <!-- Revision band: Rev 2 — Mar 15, error discovered (blue) -->
  <rect x="161" y="163" width="598" height="24" rx="3" fill="rgba(66,182,240,0.06)"/>
  <text x="770" y="179" text-anchor="start" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Rev 2: Discovery</text>

  <!-- Revision band: Rev 3 — Mar 20, correction applied (orange) -->
  <rect x="161" y="143" width="598" height="20" rx="3" fill="rgba(244,123,32,0.06)"/>
  <circle cx="400" cy="153" r="4" fill="rgba(244,123,32,0.25)" stroke="#F47B20" stroke-width="1.2"/>
  <text x="770" y="157" text-anchor="start" fill="#9ca3af" font-size="8" font-family="Inter,sans-serif">Rev 3: Correction</text>

  <!-- Query crosshair: txn=Mar 15, valid=Mar 1 → (540, 175) -->
  <line x1="540" y1="55" x2="540" y2="345" stroke="#F47B20" stroke-width="1" stroke-dasharray="5 3" opacity="0.4"/>
  <line x1="160" y1="175" x2="760" y2="175" stroke="#42B6F0" stroke-width="1" stroke-dasharray="5 3" opacity="0.4"/>

  <!-- Query dot -->
  <circle cx="540" cy="175" r="9" fill="rgba(244,123,32,0.15)" stroke="#F47B20" stroke-width="1.5" opacity="0.8"/>
  <circle cx="540" cy="175" r="3.5" fill="#F47B20"/>

  <!-- Connector from label to dot -->
  <line x1="555" y1="81" x2="543" y2="168" stroke="#F47B20" stroke-width="0.8" opacity="0.4"/>

  <!-- Query label -->
  <rect x="555" y="68" width="195" height="26" rx="4" fill="rgba(244,123,32,0.08)" stroke="#F47B20" stroke-width="1" opacity="0.6"/>
  <text x="652" y="85" text-anchor="middle" fill="#F47B20" font-size="8" font-family="JetBrains Mono,monospace" font-weight="500">jn:open-bitemporal(Mar 15, Mar 1)</text>
</svg>

```xquery
(: What was the recorded risk exposure on March 1st,
   as our system understood it on March 15th?
   Signature: jn:open-bitemporal($coll, $res, $transactionTime, $validTime) :)
jn:open-bitemporal('risk-db', 'exposures',
  xs:dateTime('2025-03-15T00:00:00Z'),
  xs:dateTime('2025-03-01T00:00:00Z'))
```

### Sanctions & Watchlist Screening

Sanctions lists change frequently, sometimes retroactively. A person added to a sanctions list today might be flagged as *"sanctioned since 2023."* Compliance teams must answer two separate questions:

- *"Given what our system knew on date X, were we compliant?"*
- *"Given what we know now, were we ever exposed?"*

Two different temporal axes. Two different answers. Both legally required. Without bitemporality, teams maintain parallel versions of screening results manually — and auditors ask why they don't match.

### What-If / As-Of Scenario Analysis

Portfolio managers need to re-run valuation models against historical market data: *"If I re-run my model using the market data we had last Tuesday — not today's corrected data — what would the P&L be?"*

This requires freezing both valid time (the market state) and transaction time (what was recorded when). SirixDB lets you open a read transaction at any (transaction-time, valid-time) coordinate pair. Without bitemporality, you would need to snapshot entire datasets at every point in time.

### Pricing & Rate History for Billing Disputes

A customer disputes a charge from three months ago. The price has since changed, and the rate table has been corrected twice. You need to prove:

1. What rate was in effect for the customer's usage period (valid time)
2. What your system believed the rate to be when it generated the invoice (transaction time)

Without bitemporality, billing teams maintain manual "rate history" tables that are never quite accurate when disputes arise.

---

## Healthcare & Life Sciences

### Treatment Decision Reconstruction

A patient's lab result arrives on Tuesday but is corrected on Thursday. A doctor made a treatment decision on Wednesday based on the Tuesday value. Was the decision reasonable given what was known at the time?

Malpractice cases hinge on exactly this distinction. Without bitemporality, the corrected value overwrites the original and the Wednesday decision looks inexplicable in retrospect. SirixDB preserves both: the original result (transaction time: Tuesday) and the correction (transaction time: Thursday, valid time: Tuesday), making the full clinical picture queryable.

### Retroactive Corrections in Medical Records

Medical records involve constant corrections: updated diagnoses, reclassified procedures, amended prescriptions. Each correction has a "when it was true" (valid time) and "when we recorded it" (transaction time). Regulations like HIPAA require that the original record remain accessible even after correction.

SirixDB's append-only storage guarantees that no data is ever overwritten. Every version is a first-class citizen, queryable by both time axes.

---

## Legal & Compliance

### Legal Discovery & Litigation Hold

Courts require point-in-time reconstruction: *"Show me the exact state of this contract record as our system understood it on June 3rd, 2024."*

With SirixDB, this is a single temporal read transaction. Without it, legal teams scramble through backup tapes, database logs, and change-data-capture streams — a process that can take weeks and still produce incomplete results.

### Anti-Fraud Detection

Fraudsters manipulate records and hope the original state is lost. Bitemporality makes this detectable: you can identify that a transaction claiming to be from January was only recorded in March by comparing valid time against transaction time.

```xquery
(: Find records where valid-time was backdated
   more than 7 days before transaction-time :)
for $rev in jn:all-times(jn:doc('ledger', 'transactions'))
for $r in $rev[]
where sdb:timestamp($rev) gt sdb:valid-from($r)
  and sdb:timestamp($rev) - sdb:valid-from($r)
    gt xs:dayTimeDuration('P7D')
return $r
```

On a mutable database, this kind of temporal anomaly detection requires triggers, shadow tables, and append-only audit logs that are trivially bypassed by anyone with write access. SirixDB's append-only architecture makes tampering structurally impossible.

---

## Supply Chain & Manufacturing

### Provenance & Recall Tracing

When a contaminated batch is discovered, regulators ask: *"Where was this ingredient at every point in time, and when did each participant record receipt or shipment?"*

A supplier might backdate a shipment record after the fact. Bitemporality distinguishes the actual chain of custody from the chain of paperwork — critical for pinpointing liability. Without it, you are trusting that nobody quietly edited a row, and you have no way to verify.

### Digital Twin Calibration

Industrial IoT digital twins are continuously calibrated against sensor data. When sensors are recalibrated, historical readings are retroactively adjusted. Engineers need to compare:

- What the twin predicted based on raw readings (transaction time: when readings were first recorded)
- What it would have predicted with corrected readings (valid time: when the readings apply, but with updated calibration)

This is essentially replaying history along both timelines simultaneously — impractical without native bitemporal support.

---

## Data Engineering & Analytics

### Time-Travel Debugging for Data Pipelines

When a downstream ML model suddenly degrades, you need to answer: *"Did the source data change? When? Was it a correction or new data?"*

Bitemporality lets you diff any two (valid-time, transaction-time) coordinates to pinpoint exactly what shifted and when it was recorded. Without it, you are reduced to comparing periodic snapshots — if you even kept them.

### Reproducible Scientific Data Analysis

A researcher publishes results in June based on a dataset that gets corrected in August. Peer reviewers need to reproduce the June analysis against the exact data the researcher had — not the corrected version.

SirixDB gives you `AS OF transaction-time June` — the dataset as it existed when the researcher queried it. Without bitemporality, you rely on manually versioned file exports and hope nothing slipped through between revisions.

### Slowly Changing Dimensions — Done Right

Data warehouses have SCD Type 1/2/3/4/6 as increasingly desperate workarounds to track dimension history. Each type trades off between complexity, storage, and query capability. Bitemporality makes all of them unnecessary — you query at the temporal coordinates you care about.

No surrogate keys. No effective-date columns. No complex merge logic. No choosing between "overwrite" and "add a row."

---

## Content & Configuration Management

### Collaborative Document Editing with Full History

Think version control for structured data. *"Who changed this field, when, and what was it before?"* becomes a temporal query. Building this on a conventional database means implementing your own version chain, conflict resolution, and diff engine — essentially reimplementing what SirixDB provides natively through its [built-in diffing](/docs/rest-api.html) and revision history.

### Configuration Drift & Incident Root Cause

*"The production outage started at 14:00. What was the configuration state at that time? Was a config change pushed at 13:55 that we didn't learn about until the post-mortem?"*

Bitemporality naturally captures both when a config was effective (valid time) and when it was recorded in the config management system (transaction time). CMDB tools try to bolt this on with change logs, but they are disconnected from the actual state and always incomplete.

---

## Journalism & Open Source Intelligence

Websites, government filings, and corporate disclosures change — sometimes silently. Investigative journalists track *"What did this company's filing say on March 1st?"* versus *"When did we first capture that version?"*

The Wayback Machine does this for HTML blobs. SirixDB does it for **structured, queryable data** — with the ability to diff any two snapshots, navigate the document tree at any point in time, and query across the full revision history.

---

## The Common Thread

Every use case above shares a single insight: **reality is messy, corrections are inevitable, and "when we recorded it" is a different question from "when it was true."**

Any system that overwrites state destroys information that turns out to be critical the moment someone asks *"but what did we think was true last week?"*

Traditional workarounds — audit tables, CDC pipelines, event logs, periodic snapshots, manual versioning — attempt to recreate what a bitemporal database provides natively. They are expensive to build, expensive to maintain, and inevitably incomplete.

<svg viewBox="0 0 860 340" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:1180px;" role="img" aria-label="Comparison: traditional databases need fragile workarounds while SirixDB provides native bitemporal storage">
  <!-- Title -->
  <text x="430" y="22" text-anchor="middle" fill="#e8e6e3" font-size="13" font-family="Inter,sans-serif" font-weight="600">Traditional Workarounds vs Native Bitemporality</text>

  <!-- Divider -->
  <line x1="430" y1="42" x2="430" y2="310" stroke="#374151" stroke-width="1" stroke-dasharray="6 4" opacity="0.5"/>

  <!-- === Left: Traditional Database === -->
  <text x="215" y="55" text-anchor="middle" fill="#9ca3af" font-size="11" font-family="Inter,sans-serif" font-weight="600">Traditional Database</text>

  <!-- Audit Tables -->
  <rect x="55" y="78" width="130" height="30" rx="4" fill="rgba(127,29,29,0.08)" stroke="#7f1d1d" stroke-width="1" opacity="0.6"/>
  <text x="120" y="97" text-anchor="middle" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">Audit Tables</text>

  <!-- CDC Pipeline -->
  <rect x="230" y="78" width="130" height="30" rx="4" fill="rgba(127,29,29,0.08)" stroke="#7f1d1d" stroke-width="1" opacity="0.6"/>
  <text x="295" y="97" text-anchor="middle" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">CDC Pipeline</text>

  <!-- Event Log -->
  <rect x="55" y="145" width="130" height="30" rx="4" fill="rgba(127,29,29,0.08)" stroke="#7f1d1d" stroke-width="1" opacity="0.6"/>
  <text x="120" y="164" text-anchor="middle" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">Event Log</text>

  <!-- Periodic Snapshots -->
  <rect x="230" y="145" width="130" height="30" rx="4" fill="rgba(127,29,29,0.08)" stroke="#7f1d1d" stroke-width="1" opacity="0.6"/>
  <text x="295" y="164" text-anchor="middle" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">Periodic Snapshots</text>

  <!-- Manual Versioning -->
  <rect x="120" y="212" width="170" height="30" rx="4" fill="rgba(127,29,29,0.08)" stroke="#7f1d1d" stroke-width="1" opacity="0.6"/>
  <text x="205" y="231" text-anchor="middle" fill="#9ca3af" font-size="9" font-family="Inter,sans-serif">Manual Versioning</text>

  <!-- Tangled connecting lines -->
  <line x1="185" y1="93" x2="230" y2="93" stroke="#6b7280" stroke-width="0.8" opacity="0.4"/>
  <line x1="120" y1="108" x2="295" y2="145" stroke="#6b7280" stroke-width="0.8" opacity="0.4"/>
  <line x1="295" y1="108" x2="120" y2="145" stroke="#6b7280" stroke-width="0.8" opacity="0.4"/>
  <line x1="120" y1="175" x2="205" y2="212" stroke="#6b7280" stroke-width="0.8" opacity="0.4"/>
  <line x1="295" y1="175" x2="205" y2="212" stroke="#6b7280" stroke-width="0.8" opacity="0.4"/>
  <line x1="185" y1="90" x2="135" y2="145" stroke="#6b7280" stroke-width="0.8" opacity="0.3"/>
  <line x1="245" y1="160" x2="185" y2="145" stroke="#6b7280" stroke-width="0.8" opacity="0.3"/>

  <!-- Label -->
  <text x="210" y="278" text-anchor="middle" fill="#7f1d1d" font-size="10" font-family="Inter,sans-serif" font-weight="500" opacity="0.8">Fragile · Expensive · Incomplete</text>

  <!-- === Right: SirixDB === -->
  <text x="645" y="55" text-anchor="middle" fill="#e8e6e3" font-size="11" font-family="Inter,sans-serif" font-weight="600">SirixDB</text>

  <!-- Transaction Time arrow (top → box) -->
  <text x="645" y="80" text-anchor="middle" fill="#42B6F0" font-size="9" font-family="Inter,sans-serif" font-weight="500">Transaction Time</text>
  <line x1="645" y1="88" x2="645" y2="128" stroke="#42B6F0" stroke-width="1.5"/>
  <polygon points="645,128 640,118 650,118" fill="#42B6F0"/>

  <!-- Valid Time arrow (left → box) -->
  <text x="490" y="172" text-anchor="end" fill="#F47B20" font-size="9" font-family="Inter,sans-serif" font-weight="500">Valid Time</text>
  <line x1="498" y1="175" x2="528" y2="175" stroke="#F47B20" stroke-width="1.5"/>
  <polygon points="528,175 518,170 518,180" fill="#F47B20"/>

  <!-- Main box -->
  <rect x="530" y="130" width="230" height="90" rx="8" fill="rgba(66,182,240,0.08)" stroke="#42B6F0" stroke-width="1.5"/>
  <text x="645" y="172" text-anchor="middle" fill="#e8e6e3" font-size="11" font-family="Inter,sans-serif" font-weight="600">Append-Only</text>
  <text x="645" y="192" text-anchor="middle" fill="#e8e6e3" font-size="11" font-family="Inter,sans-serif" font-weight="600">Bitemporal Store</text>

  <!-- Label -->
  <text x="645" y="260" text-anchor="middle" fill="#42B6F0" font-size="10" font-family="Inter,sans-serif" font-weight="500">Native · Queryable · Immutable</text>
</svg>

SirixDB makes these questions cheap to ask and impossible to get wrong. Every revision is a first-class citizen, queryable as fast as the latest, with both time axes preserved from the moment data is written.

---

*Ready to try it? See the [Getting Started guide](/docs/index.html) or explore the [REST API](/docs/rest-api.html). Questions? Join the [community forum](https://sirix.discourse.group) or the [Discord](https://discord.gg/yC33wVpv7t).*
