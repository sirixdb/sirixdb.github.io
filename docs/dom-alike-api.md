---
layout: documentation
doctitle: DOM-alike API
title: SirixDB - DOM-alike API
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/dom-alike-api.md)

## Maven artifacts

Use **JDK 25** for current SirixDB source builds. Follow the
[embedded-library setup](https://github.com/sirixdb/sirix#as-an-embedded-library)
for published Maven/Gradle coordinates and the required JVM flags. The query
layer uses the `io.sirix:sirix-query` artifact; the cursor API uses
`io.sirix:sirix-core`. Keep module versions aligned. For the current source
version and snapshot repositories, use the repository's
[Gradle properties](https://github.com/sirixdb/sirix/blob/main/gradle.properties)
and [build configuration](https://github.com/sirixdb/sirix/blob/main/build.gradle).
Source builds use the provided Gradle wrapper; published artifacts can be
consumed from Maven or Gradle applications.

## Working with nodes

The query module adapts SirixDB's transactional cursors to Brackit's node and JSON
item interfaces. XML nodes use
[`XmlDBNode`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-query/src/main/java/io/sirix/query/node/XmlDBNode.java)
and [`BasicXmlDBStore`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-query/src/main/java/io/sirix/query/node/BasicXmlDBStore.java).
JSON objects, arrays and scalar values use the
[`JsonDBItem`](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-query/src/main/java/io/sirix/query/json/JsonDBItem.java)
interface and `BasicJsonDBStore`.

These objects reference a resource transaction; they do not materialize an entire
document in memory. Keep the store and query context open while using them.
Read-only nodes refer to their revision's snapshot. Updates are applied through
`SirixQueryContext`, whose commit strategy controls publication.

Use the [JSONiq API examples](/docs/jsoniq-api.html#running-queries-from-java)
to create a store, query context and compile chain together. For explicit
navigation and transaction lifecycle management, see the
[transactional cursor API](/docs/transactional-cursor-api.html).
