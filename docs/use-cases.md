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

---

## Financial Services & Regulatory Compliance

### Regulatory Audit Trails

Financial institutions must answer questions like: *"What did we know about this customer's risk exposure on March 1st, as understood on March 15th — versus after a correction was applied on March 20th?"*

With SirixDB, this is a single bitemporal query. Without it, teams build shadow audit tables, change-data-capture pipelines, and custom versioning layers — fragile infrastructure that is expensive to maintain and inevitably incomplete.

```xquery
(: What was the recorded risk exposure on March 1st,
   as our system understood it on March 15th? :)
jn:open-bitemporal('risk-db', 'exposures',
  xs:dateTime('2025-03-01T00:00:00'),
  xs:dateTime('2025-03-15T00:00:00'))
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
for $r in jn:all-times(jn:doc('ledger', 'transactions'))
where sdb:timestamp($r) - sdb:valid-from($r)
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

SirixDB makes these questions cheap to ask and impossible to get wrong. Every revision is a first-class citizen, queryable as fast as the latest, with both time axes preserved from the moment data is written.

---

*Ready to try it? See the [Getting Started guide](/docs/index.html) or explore the [REST API](/docs/rest-api.html). Questions? Join the [community forum](https://sirix.discourse.group) or the [Discord](https://discord.gg/yC33wVpv7t).*
