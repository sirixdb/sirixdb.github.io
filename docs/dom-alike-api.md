---
layout: documentation
doctitle: DOM-alike API
title: SirixDB - DOM-alike API
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/dom-alike-api.md)

## Maven artifacts

The DOM-alike layer uses the query module. Follow the
[JSONiq API setup](/docs/jsoniq-api.html#setup) for dependencies and build requirements.

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
