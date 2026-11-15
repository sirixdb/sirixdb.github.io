---
layout: documentation
doctitle: Features
title: SirixDB - Features
---

[Edit document on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/features.md)

## Features in a nutshell

These capabilities describe the current source build. Check the
[release status and roadmap](https://github.com/sirixdb/sirix/blob/main/ROADMAP.md)
when choosing a published version.

- **Native JSON and XML:** tree storage with stable node keys for following the same node across revisions.
- **Revision history and diffs:** copy-on-write snapshots, structural revision diffs and reverting a resource into a new revision. Committed history remains readable until the resource or database is deleted. See [Architecture](/docs/architecture.html).
- **Bitemporal queries:** combine transaction time (committed revisions) with application-supplied valid time. Valid-time paths and indexes must be configured; see [Bitemporal Queries](/docs/jsoniq-functions.html#bitemporal-queries).
- **Snapshot transactions:** multiple readers and one writer per resource, with [synchronous and asynchronous commit modes](/docs/architecture.html#auto-commit-and-the-asynchronous-pre-flush).
- **Versioned document indexes:** name, path and content-and-structure (CAS) indexes, plus a configurable persisted path summary. See the [index functions](/docs/jsoniq-functions.html#indexes).
- **Experimental columnar analytics:** versioned projection indexes extract declared fields into column-oriented pages. Eligible JSONiq aggregates, filtered counts and grouped queries use the vectorized SIMD execution path; unsupported query shapes use the regular pipeline. REST routing has an allowlist gate. See the [projection guide](https://github.com/sirixdb/sirix/blob/main/docs/PROJECTION_INDEXES.md) for current limits.
- **Vector search through the core Java API:** versioned HNSW indexes support approximate nearest-neighbor search. Applications insert vectors explicitly through the [VectorIndex API](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/index/vector/VectorIndex.java).
- **JSONiq and XQuery:** Brackit integration with [temporal JSONiq functions](/docs/jsoniq-functions.html) and XML temporal XPath axes. Start with the [query API](/docs/jsoniq-api.html).
- **Embedded Java access:** use the engine in-process, including the [transactional cursor API](/docs/transactional-cursor-api.html) and [DOM-like XML API](/docs/dom-alike-api.html).
- **REST access:** manage JSON/XML resources, query revisions and update data through the [Vert.x REST API](/docs/rest-api.html).
- **Browser GUI and shell:** explore the hosted [web GUI demo](https://demo.sirix.io), or use the interactive `sirix-shell` JSONiq/XQuery REPL described in the [source quick start](https://github.com/sirixdb/sirix#quick-start).
- **Off-heap memory and cache budgets:** page storage, engine I/O and scratch working memory share a configurable process-wide allocator. Cache limits include byte budgets and entry caps; see [Operations](/docs/operations.html#4-cache-budgets).
- **Storage options:** full, incremental, differential and [sliding snapshot versioning](/docs/architecture.html#sliding-snapshot-versioning), optional DeweyIDs and subtree hashes, and configurable page byte-handler pipelines. Subtree hashes support change detection, not cryptographic tamper evidence.
- **XML revision import:** subtree moves and FMSE-based import of successive XML revisions.
- **Planned, not shipped:** distributed sharding/replication and full-text indexing remain [roadmap work](https://github.com/sirixdb/sirix/blob/main/ROADMAP.md).

See [Getting Started](/docs/getting-started.html) for a working setup and
[Operations](/docs/operations.html) for deployment requirements and limitations.
