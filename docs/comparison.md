---
layout: documentation
doctitle: SirixDB vs Alternatives
title: SirixDB - Comparison with Other Temporal Databases
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/comparison.md)

## Overview

Several databases support temporal or versioned data. This page provides an honest comparison to help you choose the right tool for your use case. Every database has trade-offs — SirixDB is no exception.

## SirixDB vs XTDB

[XTDB](https://xtdb.com) (formerly Crux) is a bitemporal database built in Clojure. Both SirixDB and XTDB track system time and valid time, but their architectures differ significantly.

|  | SirixDB | XTDB |
|---|---|---|
| **Language** | Java / Kotlin | Clojure (JVM) |
| **Data model** | Document trees (JSON, XML) | Entities / tuples |
| **Query language** | JSONiq, XQuery, temporal XPath axes | SQL (v2), Datalog (v1) |
| **Storage** | Append-only copy-on-write tree with sliding snapshots | Pluggable backends (RocksDB, etc.), columnar in v2 |
| **Write-Ahead Log** | Not needed — UberPage swap is atomic | Traditional WAL |
| **Diffing** | Built-in: compare any two revisions | Not built-in |
| **Visualization** | Web GUI with sunburst, treemap, explorer | No built-in GUI |
| **License** | BSD-3-Clause | MPL-2.0 |
| **Cloud offering** | Planned | Available |

### When to choose SirixDB

- You work with **document data** (JSON or XML) and need deep tree-level versioning
- **Storage efficiency** is critical — the sliding snapshot algorithm avoids full copies and background compaction
- You need **built-in diffing** between arbitrary revisions, not just consecutive ones
- You want **visual exploration** of your data with sunburst, treemap, and tree views
- You prefer an architecture with **no WAL** — fewer moving parts, simpler operations

### When to choose XTDB

- You need **SQL compatibility** (XTDB v2 offers full SQL support)
- You want a **managed cloud service** today
- Your data model is entity/tuple-oriented rather than document trees
- You need a **larger ecosystem** and more community resources

## SirixDB vs Event Sourcing

Event sourcing stores every state change as an immutable event. While SirixDB shares the "never delete" philosophy, it offers key advantages:

- **Efficient reconstruction**: SirixDB can reconstruct any revision in logarithmic time via its page tree, rather than replaying all events
- **Structural queries**: Query across the document structure at any point in time, not just replay events sequentially
- **Space efficiency**: Copy-on-write sharing means unchanged data is stored once, not implied by event replay
- **Two time axes**: Event sourcing typically tracks only when events occurred, not when facts were valid in the real world

SirixDB can complement event sourcing: store your current state in SirixDB for efficient temporal queries, while keeping the event log as the source of truth.

## SirixDB vs Git for Data

Git-like version control for data (DVC, lakeFS, Dolt) is increasingly popular. SirixDB differs in important ways:

|  | SirixDB | Git-style versioning |
|---|---|---|
| **Granularity** | Node-level (individual JSON/XML nodes) | File or row-level |
| **Branching** | Linear revision history per resource | Full branching/merging |
| **Query** | JSONiq / XQuery with temporal axes | SQL (Dolt) or file-based |
| **Storage** | Shared page-fragments via copy-on-write | Full snapshots or row-level diffs |
| **Time travel** | Any revision by number or timestamp | By commit hash |

### When to choose SirixDB

- You need **sub-document granularity** — tracking changes at the node level, not file level
- You want **temporal query axes** to navigate both time and structure simultaneously
- Your data is naturally **hierarchical** (JSON/XML documents)

### When to choose Git-style tools

- You need **branching and merging** workflows
- Your data is tabular (SQL) or file-based
- Team collaboration with pull-request-style review is important

## SirixDB vs Traditional Databases with Temporal Extensions

PostgreSQL (with temporal tables), Oracle Flashback, and SQL Server temporal tables add time-travel to relational databases. Compared to SirixDB:

- **Native vs bolted-on**: SirixDB was designed from the ground up for temporal data. Relational temporal extensions add history tables on top of existing architectures, which can lead to storage bloat and query complexity
- **Document vs relational**: SirixDB natively stores semi-structured data without schema. Relational temporal tables require fixed schemas
- **Storage model**: SirixDB's copy-on-write tree shares unchanged data across revisions automatically. Temporal tables typically duplicate entire rows on every change
- **Valid time**: Most relational temporal extensions support only system time. Bitemporal support (both system and valid time) requires complex schema design. SirixDB supports both natively

## Roadmap

SirixDB is actively evolving. Planned developments include:

- **Cloud offering**: A managed SirixDB service is in development, so you can use temporal document storage without operational overhead
- **Enhanced query capabilities**: Continued improvements to the JSONiq processor and temporal query functions
- **Improved Web GUI**: Additional visualization modes and collaborative features

---

*Have questions about how SirixDB compares to your current stack? Join the [community forum](https://sirix.discourse.group) or open a [GitHub discussion](https://github.com/sirixdb/sirix/discussions).*
