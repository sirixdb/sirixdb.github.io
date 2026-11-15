---
layout: documentation
doctitle: Operations & Production Deployment
title: SirixDB - Operations
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/operations.md)

Deployment, tuning and troubleshooting for `sirix-core` and `sirix-rest-api`.
This page describes the current source build. Consult the
[SirixDB README](https://github.com/sirixdb/sirix) for published releases and
[Getting Started](/docs/getting-started.html) for a local example. Benchmark your
own workload before choosing production resource limits.

## 1. Supported environment

| Dimension | Current source requirement |
|---|---|
| JDK | Java 25, configured by the [Gradle toolchain](https://github.com/sirixdb/sirix/blob/main/build.gradle) |
| Build | The repository's Gradle wrapper; embedded Maven examples have their own POM |
| Native image | Build instructions for REST and CLI binaries are in [NATIVE_IMAGE.md](https://github.com/sirixdb/sirix/blob/main/docs/NATIVE_IMAGE.md) |
| Concurrency | Multiple readers and one writer per resource; independent resources can have separate writers |
| Deployment | A local engine/server; do not assume a distributed replication or consensus service |

The on-disk encoding is versioned. Do not assume that files from different
SirixDB builds are compatible; retain the producing build and test backup
restoration before upgrading. The current
[`ResourceConfiguration`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/access/ResourceConfiguration.java)
defines `BinaryEncodingVersion.V0`. This is not a promise about future migration tooling.

## 2. Mandatory JVM flags

Use the generated distribution launchers where possible. They include their
module's JVM options; a bare `java -jar` does not automatically inherit Gradle
configuration. The query and core modules use the Vector API and native access:

```text
--add-modules=jdk.incubator.vector
--enable-native-access=ALL-UNNAMED
```

Depending on the module and build, preview features and additional exports/opens
are configured in the [root build](https://github.com/sirixdb/sirix/blob/main/build.gradle).
Use the flags from the build you are running. For the published core library,
use the [standalone embedded example](https://github.com/sirixdb/sirix/tree/main/docs/examples/embedded)
and its Maven launch command together.

## 3. Heap sizing and GC choice

Budget for both Java heap and off-heap page memory, plus query intermediates and
native libraries. `-Xmx` limits the heap; it is not the process's total memory
limit. `DatabaseConfiguration.setMaxSegmentAllocationSize(...)` configures the
allocator budget when a database is created. The allocator and caches are shared
within the process, so the first initialization matters.

Start with the [Dockerfile's runtime settings](https://github.com/sirixdb/sirix/blob/main/Dockerfile)
and [Compose resource limits](https://github.com/sirixdb/sirix/blob/main/docker-compose.yml)
for the local container setup. Increase heap, direct-memory and container limits
together when measurements require it. Test JVM heap and GC flags in Gradle are
benchmark/test settings, not production sizing guarantees.

Use GC logs or JFR to compare collectors on your workload. Do not copy obsolete
collector flags from an older JDK launch command.

## 4. Cache budgets

The current initialization in
[`Databases`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/access/Databases.java)
computes cache limits from the allocator budget:

| Cache | Default | Override |
|---|---|---|
| Record pages | 50% of budget | `sirix.cache.recordPage` (bytes) |
| Record-page fragments | 18.75% of budget | `sirix.cache.recordPageFragment` (bytes) |
| Metadata pages | 6.25% of budget, minimum 100 MiB | `sirix.cache.page` (bytes) |
| Revision roots | 20,000 entries | `sirix.cache.revisionRoot.max.entries` (positive entry count) |
| Names | 500 entries | Fixed in initialization |
| Path summaries | 20 entries | Fixed in initialization |

For example, these **illustrative limits** require enough allocator and process
memory for the caches and the rest of the workload:

```text
-Dsirix.cache.recordPage=1073741824
-Dsirix.cache.recordPageFragment=402653184
-Dsirix.cache.page=134217728
-Dsirix.cache.revisionRoot.max.entries=20000
```

Inspect the byte counts in startup logs and the metrics below. Some source
comments and log suffixes still describe older percentages; the initialization
code, rather than those suffixes, determines the configured sizes.

## 5. Native libraries

The current default outer page byte-handler pipeline is uncompressed
(`sirix.compression=none`). `-Dsirix.compression=lz4` selects the FFM LZ4 handler;
if native LZ4 is unavailable, the default pipeline selection warns and falls
back to uncompressed pages. This selection does not imply that an existing
resource with an explicitly configured compressor can be read without it.

The LZ77 codec has a bundled Linux x86_64 decoder and a Java fallback.
`-Dsirix.lz77Codec.native.disable=true` disables that native decoder for comparison.
No fixed throughput improvement is guaranteed. See
[`ResourceConfiguration`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/access/ResourceConfiguration.java)
for compression selection and the source build for native-library tasks.

## 6. OS-level requirements

Size file-descriptor limits, memory limits and storage for the expected number
of resources and transactions. Retained revisions grow the data directory;
monitor free space and establish backups. Measure disk latency on the actual
filesystem rather than assuming a fixed SSD speedup or a particular filesystem's
safety guarantees.

Keep the host clock synchronized because commit timestamps participate in
point-in-time queries. Configure server authentication and TLS for the deployment;
the bundled Compose example uses local HTTP and development credentials.

## 7. Observability

`GET /metrics` exposes Prometheus text metrics, and `GET /health` is a health
probe. Both are unauthenticated endpoints. Restrict network exposure as appropriate
for your deployment. The wiring is in
[`MetricsHandler.kt`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-rest-api/src/main/kotlin/io/sirix/rest/MetricsHandler.kt).

| Metrics | Meaning |
|---|---|
| `http_request_duration_seconds` | Request-duration histogram, by method, path and status |
| `http_requests_total` | Request count with the same labels |
| `http_active_requests` | In-flight requests |
| `jvm_memory_*`, `jvm_gc_*`, `process_uptime_seconds` | JVM memory, GC and process basics |
| `sirix_record_page_cache_hits_total`, `sirix_record_page_cache_misses_total`, `sirix_record_page_cache_evictions_total` | Record-page cache counters |
| `sirix_active_node_read_only_transactions`, `sirix_active_node_read_write_transactions` | Active node transactions |
| `sirix_record_page_cache_size_bytes`, `sirix_record_page_cache_max_bytes` | Record-page cache occupancy and limit |
| `sirix_allocator_physical_memory_bytes` | Allocator physical commitment |
| `sirix_allocator_scratch_*` | Scratch-buffer use, reuse and refused allocations |

The [SirixMetricsRegistry inventory](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/metrics/SirixMetricsRegistry.java)
defines the complete internal metric names. Embedders can install their own
bridge; the REST server installs its Prometheus bridge automatically.

## 8. Backup and restore

A conservative file-copy procedure is to stop the server or embedding application
and close **all transactions, sessions and the database** before copying its
entire database directory, including configuration and resource subdirectories.
Do not copy individual resource files while a writer is active or assume that
append-only pages make a live multi-file copy consistent.

Keep the SirixDB build/version and deployment configuration with the backup.
Restore to a separate location first and open it with the matching build; verify
resource contents and historical revisions before relying on it. Do not overwrite
a live database directory during restoration.

A temporal read such as `session.beginNodeReadOnlyTrx(revision)` or
`session.beginNodeReadOnlyTrx(Instant)` selects retained history. It is not a
substitute for a backup after storage loss or resource deletion.

## 9. Supported workloads

| Dimension | Behavior |
|---|---|
| Documents | JSON or XML, selected by database type |
| Concurrency | One writer per resource, multiple read-only transactions |
| Time | Commit revisions plus application-configured valid time |
| Record versioning | `FULL`, `INCREMENTAL`, `DIFFERENTIAL`, `SLIDING_SNAPSHOT` |
| Secondary indexes | Name, path and CAS; HOT is their storage structure, not a fourth query index type |
| Query languages | Brackit JSONiq and XQuery |

Codec block sizes are not document-size limits. Test large imports with your
actual data and memory budget. Valid-time paths require application values and
the corresponding indexes; see [Bitemporal Queries](/docs/jsoniq-functions.html#bitemporal-queries).

## 10. Known limitations and operational caveats

- A second writer on a resource waits for the writer lock and can fail after
  the current five-second acquisition timeout. Close writers reliably.
- Source builds use a Brackit snapshot; use the repository's build configuration
  and distinguish this from published library dependencies.
- Do not assume on-disk format migration between releases.
- `AfterCommitState.KEEP_OPEN_ASYNC_FLUSH` pre-flushes pages without publishing
  intermediate revisions. It supports `FILE_CHANNEL` and `MEMORY_MAPPED`.
- `AfterCommitState.KEEP_OPEN_ASYNC_COMMIT` publishes durable intermediate
  revisions and currently requires `FILE_CHANNEL`. Both async modes require
  count-based auto-commit, not timed auto-commit. See the
  [enum contract](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/main/java/io/sirix/access/trx/node/AfterCommitState.java)
  and [async commit design](https://github.com/sirixdb/sirix/blob/main/docs/ASYNC_COMMIT_DESIGN.md).
- Store imports can opt out of async pre-flush with
  `-Dsirix.import.asyncFlush=false`.
- The source includes crash-recovery and fault-injection tests. Those tests
  exercise specific failure models; they do not guarantee every storage device
  or deployment configuration. Test restoration and failure handling in your environment.

## 11. Quick-start: launch the REST API server

From the SirixDB source checkout:

```bash
docker compose up -d
curl --fail http://localhost:9443/health
curl --fail http://localhost:9443/metrics
```

Wait for the service to become healthy before issuing requests. The current
Docker configuration sets `use.http: true`; configure TLS explicitly for a
remote deployment. For token acquisition and a complete resource workflow, use
[Getting Started](/docs/getting-started.html#rest-api).

## 12. Where to look when something is wrong

| Symptom | First checks |
|---|---|
| JVM access or incubator-module error | Use the matching distribution launcher and JDK; check section 2 |
| Incompatible encoding error on open | Confirm the producing build and restore a verified backup |
| Direct-buffer or heap exhaustion | Check process/container limits, heap, allocator budget and cache sizes together |
| Low cache hit rate | Compare working-set size with cache occupancy, hit/miss counters and configured limits |
| Long GC pauses | Record GC logs/JFR before changing collector or heap settings |
| Writer acquisition timeout | Find and close the existing writer on that resource |
| Async commit failure | Inspect the error, stop reusing the failed transaction and consult the async commit contract |

## 13. Further reading

- [Architecture](/docs/architecture.html)
- [Features](/docs/features.html)
- [REST API](/docs/rest-api.html)
- [JSONiq API](/docs/jsoniq-api.html) and [Function Reference](/docs/jsoniq-functions.html)
- [Native image build](https://github.com/sirixdb/sirix/blob/main/docs/NATIVE_IMAGE.md)
- [Roadmap](https://github.com/sirixdb/sirix/blob/main/ROADMAP.md)
