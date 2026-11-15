---
layout: documentation
doctitle: Features
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/features.md)

## Features in a nutshell

- Native JSON and XML tree storage with stable node keys.
- Copy-on-write revision history. Committed revisions remain readable until the resource or database is deleted.
- Multiple read-only transactions and one writer per resource. Read-only transactions select a committed snapshot.
- Revert a resource to a past revision and commit a new revision while retaining the intervening history.
- Versioned name, path and content-and-structure (CAS) indexes.
- Temporal JSONiq functions and XML temporal XPath axes for navigation across revisions.
- Application-supplied valid-time configuration for [bitemporal queries](/docs/jsoniq-functions.html#bitemporal-queries).
- A persisted path summary, enabled by default and configurable per resource.
- [Per-resource versioning strategies](/docs/architecture.html#sliding-snapshot-versioning): full, incremental, differential and sliding snapshot.
- Shadow paging with sequential page writes; no separate redo write-ahead log or LSM-style background compaction.
- [Synchronous and asynchronous commit modes](/docs/architecture.html#auto-commit-and-the-asynchronous-pre-flush), with different revision-publication semantics.
- [JSONiq / XQuery integration](/docs/jsoniq-api.html) through Brackit and a [REST API](/docs/rest-api.html) through Vert.x.
- XML subtree moves and XML revision import through FMSE.
- Structural diffs between resource revisions.
- Optional DeweyIDs, subtree hashes and configurable page byte-handler pipelines.

See [Architecture](/docs/architecture.html) for the storage model and
[Operations](/docs/operations.html) for deployment requirements and limitations.
The [source configuration](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/access/ResourceConfiguration.java)
defines the current defaults and builder options.
