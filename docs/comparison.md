---
layout: documentation
doctitle: SirixDB vs Alternatives
title: SirixDB - Comparison with Other Temporal Databases
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/comparison.md)

## Overview

Choose according to your data model, query language and history-management needs.
The [landing-page comparison](/#compare) links to the underlying product documentation.
This page does not claim benchmark superiority: measure your workload and history size.

## SirixDB vs XTDB

SirixDB versions JSON and XML trees, exposes JSONiq/XQuery, and supports node-level
history and structural diffs. See its [architecture](/docs/architecture.html)
and [temporal functions](/docs/jsoniq-functions.html#temporal-navigation).

[XTDB](https://docs.xtdb.com/) provides a bitemporal SQL database. Consider it
when SQL access and its deployment model fit your application. Compare query
semantics, operational requirements and supported clients using the current
product documentation.

## SirixDB vs Event Sourcing

An event log records domain events; SirixDB stores document revisions. A revision
lets you read stored state without implementing domain-event replay. It does not
replace an event log's domain semantics or delivery mechanisms. The two can be
used together, with the event log as the source of truth and SirixDB holding
queryable state revisions.

## SirixDB vs Git for Data

SirixDB has a linear revision history per resource. Its cursor and query APIs
navigate individual JSON/XML nodes across those revisions.

[Dolt's branches and database revisions](https://www.dolthub.com/docs/sql-reference/version-control/branches/)
provide SQL access to branches, tags and commits. Its history can be rewritten
or purged using [history filtering](https://www.dolthub.com/blog/2020-11-30-dolt-filter-branch/), removal of old references and [full garbage collection](https://www.dolthub.com/docs/cli-reference/cli/#dolt-gc).
Evaluate those operations when retained history is part of your requirements.

For table-format time travel, [Delta Lake's data retention rules](https://docs.delta.io/delta-batch/#data-retention)
and [Iceberg's snapshot expiration](https://iceberg.apache.org/docs/latest/maintenance/#expire-snapshots)
matter: historical reads depend on retained snapshots, logs and data files,
and on engine-enforced retention rules. They are not unconditional permanent-history guarantees.

Deleting a SirixDB resource or database also deletes its history. Retained revisions
and backups serve different purposes; see [Operations](/docs/operations.html#8-backup-and-restore).

## Roadmap

Consult the [SirixDB roadmap](https://github.com/sirixdb/sirix/blob/main/ROADMAP.md)
for plans. Planned features are not a guarantee of current availability.

---

*Questions about your use case? Join the [community forum](https://sirix.discourse.group)
or open a [GitHub discussion](https://github.com/sirixdb/sirix/discussions).*
