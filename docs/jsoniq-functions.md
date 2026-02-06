---
layout: documentation
doctitle: JSONiq Function Reference
title: SirixDB - JSONiq Function Reference
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/jsoniq-functions.md)

Complete reference of all JSONiq and SirixDB extension functions. Functions use two namespaces: `jn:` (JSON/temporal) and `sdb:` (SirixDB core). For usage patterns and examples, see the [JSONiq API guide](/docs/jsoniq-api.html).

## Data Management

Store, open, and manage JSON databases and resources.

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:store` | `($coll, $res, $data)` | Store JSON data in a collection. Creates the collection if it does not exist. |
| `jn:store` | `($coll, $res, $data, $create-new)` | Store JSON data; when `$create-new` is `true`, always create a new collection. |
| `jn:load` | `($coll, $res, $uris)` | Load JSON from one or more file URIs into a collection. |
| `jn:doc` | `($coll, $res)` | Open a resource at the most recent revision. |
| `jn:doc` | `($coll, $res, $rev)` | Open a resource at a specific revision number. |
| `jn:open` | `($coll, $res, $dateTime)` | Open a resource at a point in time (closest revision). |
| `jn:open-revisions` | `($coll, $res, $from, $to)` | Open all revisions within a date-time range. |
| `jn:exists-database` | `($coll)` | Returns `true` if the database/collection exists. |
| `jn:exists-resource` | `($coll, $res)` | Returns `true` if the resource exists in the collection. |
| `jn:drop-database` | `($coll)` | Drop an entire database and all its resources. |
| `jn:drop-resource` | `($coll, $res)` | Remove a single resource from a database. |

```xquery
(: Store a JSON array and open it :)
jn:store('mydb', 'users', '[{"name":"Alice"}, {"name":"Bob"}]')
let $doc := jn:doc('mydb', 'users')
return $doc[0].name
(: => "Alice" :)

(: Open a resource at revision 3 :)
jn:doc('mydb', 'users', 3)

(: Open at a specific point in time :)
jn:open('mydb', 'users', xs:dateTime('2024-06-15T10:00:00Z'))
```

## Temporal Navigation

Navigate through revision history. These functions operate on a JSON item and return it from other revisions.

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:all-times` | `($item)` | Returns the item from every revision where it exists. |
| `jn:future` | `($item)` | All future revisions of the item (excluding current). |
| `jn:future` | `($item, $includeSelf)` | All future revisions; include current when `$includeSelf` is `true`. |
| `jn:past` | `($item)` | All past revisions of the item (excluding current). |
| `jn:past` | `($item, $includeSelf)` | All past revisions; include current when `$includeSelf` is `true`. |
| `jn:next` | `($item)` | The item in the next revision, or empty if at the latest. |
| `jn:previous` | `($item)` | The item in the previous revision, or empty if at the earliest. |
| `jn:first` | `($item)` | The item in the first revision. |
| `jn:last` | `($item)` | The item in the most recent revision. |
| `jn:first-existing` | `($item)` | The item in the first revision where it existed (was created). |
| `jn:last-existing` | `($item)` | The item in the last revision where it existed (before deletion). |

```xquery
(: See every version of a document across all revisions :)
for $v in jn:all-times(jn:doc('shop', 'products'))
return {"rev": sdb:revision($v), "count": count($v[])}

(: Step through revisions one at a time :)
let $current := jn:doc('shop', 'products')
let $prev := jn:previous($current)
return {"current": sdb:revision($current), "previous": sdb:revision($prev)}

(: Get all future versions from revision 2 onward :)
for $v in jn:future(jn:doc('shop', 'products', 2), true())
return sdb:revision($v)
```

## Bitemporal Queries

Query along two time axes: *system time* (when SirixDB recorded it) and *valid time* (when it was true in the real world). Requires resources configured with valid-time support.

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:valid-at` | `($coll, $res, $validTime)` | Returns records where the valid-time interval contains `$validTime`. |
| `jn:open-bitemporal` | `($coll, $res, $validTime, $transactionTime)` | Opens a resource at a specific transaction time, then filters by valid time. |
| `sdb:valid-from` | `($item)` | Returns the `validFrom` timestamp of a node (empty if not configured). |
| `sdb:valid-to` | `($item)` | Returns the `validTo` timestamp of a node (empty if not configured). |

```xquery
(: What did we know on March 5 about data valid on February 1? :)
jn:open-bitemporal('customers', 'addresses',
  xs:dateTime('2024-02-01T00:00:00Z'),
  xs:dateTime('2024-03-05T00:00:00Z'))
```

## Diffing

Compute structural differences between any two revisions.

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:diff` | `($coll, $res, $rev1, $rev2)` | Returns a JSON diff between two revisions. |
| `jn:diff` | `($coll, $res, $rev1, $rev2, $startNodeKey)` | Diff starting from a specific node key. |
| `jn:diff` | `($coll, $res, $rev1, $rev2, $startNodeKey, $maxLevel)` | Diff with a depth limit. |

The result is a JSON object with `database`, `resource`, `old-revision`, `new-revision`, and a `diffs` array containing `insert`, `delete`, `update`, and `replace` entries:

```xquery
jn:diff('shop', 'products', 1, 4)
(: =>
  {"database":"shop", "resource":"products",
   "old-revision":1, "new-revision":4,
   "diffs":[
     {"update": {"nodeKey":6, "path":"/[0]/price", "type":"number", "value":899}},
     {"insert": {"nodeKey":12, "path":"/[1]", "type":"jsonFragment",
                 "data":"{\"name\":\"Tablet\",\"price\":449}"}},
     {"delete": {"nodeKey":7, "path":"/[1]"}}
   ]}
:)
```

## Node Inspection

Retrieve metadata about nodes. These use the `sdb:` namespace.

| Function | Signature | Description |
|----------|-----------|-------------|
| `sdb:nodekey` | `($node)` | Returns the stable, unique integer key of a node. |
| `sdb:path` | `($node)` | Returns the path to the node (e.g. `/users/[0]/name`). |
| `sdb:hash` | `($node)` | Returns the hash of the node subtree (requires hashing enabled). |
| `sdb:revision` | `($node)` | Returns the revision number the node is being viewed in. |
| `sdb:timestamp` | `($node)` | Returns the ISO-8601 timestamp when the revision was committed. |
| `sdb:most-recent-revision` | `($node)` | Returns the most recent revision number of the resource. |
| `sdb:child-count` | `($node)` | Returns the number of direct children. |
| `sdb:descendant-count` | `($node)` | Returns the total number of descendants. |
| `sdb:is-deleted` | `($item)` | Returns `true` if the item has been deleted in a later revision. |
| `sdb:author-name` | `($node)` | Returns the name of the author who committed this revision. |
| `sdb:author-id` | `($node)` | Returns the ID of the author who committed this revision. |

```xquery
let $doc := jn:doc('shop', 'products')
return {
  "revision": sdb:revision($doc),
  "timestamp": sdb:timestamp($doc),
  "children": sdb:child-count($doc),
  "nodekey": sdb:nodekey($doc)
}
```

## Node Selection and Traversal

Navigate the document tree using stable node keys.

| Function | Signature | Description |
|----------|-----------|-------------|
| `sdb:select-item` | `($node, $key)` | Select a node by its stable integer node key. |
| `jn:select-json-item` | `($node, $key)` | Select a JSON item by its node key (JSON-specific variant). |
| `sdb:select-parent` | `($node)` | Navigate to the parent of a node. |
| `sdb:level-order` | `($node)` | Traverse all descendants in breadth-first (level) order. |
| `sdb:level-order` | `($node, $depth)` | Breadth-first traversal limited to `$depth` levels. |
| `sdb:item-history` | `($item)` | Returns the item from every revision where it was inserted or modified (ascending order). |

```xquery
(: Track how a value evolved across revisions :)
let $item := sdb:select-item(jn:doc('shop', 'products'), 6)
for $v in sdb:item-history($item)
return {"rev": sdb:revision($v), "value": $v}

(: Navigate to a specific node and inspect its parent :)
let $node := sdb:select-item(jn:doc('shop', 'products'), 3)
return sdb:path(sdb:select-parent($node))
```

## Transactions

Commit or rollback changes within a write transaction.

| Function | Signature | Description |
|----------|-----------|-------------|
| `sdb:commit` | `($node)` | Commit and create a new revision. Returns the new revision number. |
| `sdb:commit` | `($node, $message)` | Commit with a descriptive message. |
| `sdb:commit` | `($node, $message, $dateTime)` | Commit with a message and a custom timestamp. |
| `sdb:rollback` | `($node)` | Discard all uncommitted changes. Returns the aborted revision number. |

```xquery
(: Commit with a message :)
let $doc := jn:doc('shop', 'products')
return (
  replace json value of $doc[0].price with 799,
  sdb:commit($doc, "Summer sale pricing")
)
```

## Indexes

Create and query indexes for faster lookups. Three index types are supported: **name** (field names), **path** (document paths), and **CAS** (content-and-structure, for typed value queries).

### Create Indexes

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:create-name-index` | `($doc)` | Create a name index on all field names. |
| `jn:create-name-index` | `($doc, $names)` | Create a name index on specific field names. |
| `jn:create-path-index` | `($doc)` | Create a path index on all paths. |
| `jn:create-path-index` | `($doc, $paths)` | Create a path index on specific paths. |
| `jn:create-cas-index` | `($doc)` | Create a CAS index on all values. |
| `jn:create-cas-index` | `($doc, $type)` | Create a CAS index for a specific type (`xs:string`, `xs:integer`, etc.). |
| `jn:create-cas-index` | `($doc, $type, $paths)` | Create a CAS index for a type on specific paths. |

### Query Indexes

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:find-name-index` | `($doc, $name)` | Find the index number for a name index on `$name`. |
| `jn:find-path-index` | `($doc, $path)` | Find the index number for a path index on `$path`. |
| `jn:find-cas-index` | `($doc, $type, $value)` | Find the index number for a CAS index matching `$type` and `$value`. |
| `jn:scan-name-index` | `($doc, $idx, $name)` | Scan all entries in a name index. |
| `jn:scan-path-index` | `($doc, $idx, $paths)` | Scan all entries in a path index. |
| `jn:scan-cas-index` | `($doc, $idx, $key, $include, $type)` | Scan a CAS index for a specific key. |
| `jn:scan-cas-index-range` | `($doc, $idx, $low, $high, $incLow, $incHigh, $type)` | Scan a CAS index for a range of values. |

```xquery
(: Create a CAS index on the "price" path for fast numeric lookups :)
let $doc := jn:doc('shop', 'products')
let $stats := jn:create-cas-index($doc, 'xs:decimal', '/[]/price')
return $stats

(: Query the index :)
let $doc := jn:doc('shop', 'products')
let $idx := jn:find-cas-index($doc, 'xs:decimal', '/[]/price')
return jn:scan-cas-index-range($doc, $idx, 0, 500, true(), true(), 'xs:decimal')
```

## JSONiq Update Expressions

In addition to the functions above, SirixDB supports standard JSONiq update expressions. Each update automatically creates a new revision.

| Expression | Example |
|------------|---------|
| **Replace value** | `replace json value of $doc[0].price with 899` |
| **Append to array** | `append json {"name":"Tablet"} into $doc` |
| **Insert into object** | `insert json {"stock": 50} into $doc[0]` |
| **Delete** | `delete json $doc[1]` |
| **Rename key** | `rename json $doc[0].price as "cost"` |

```xquery
(: Modify and verify :)
let $doc := jn:doc('shop', 'products')
return replace json value of $doc[0].price with 899

(: The update created revision 2; query the previous state :)
jn:doc('shop', 'products', 1)[0].price
(: => 999 :)
```

## Brackit Built-in Functions

SirixDB uses the [Brackit](https://github.com/sirixdb/brackit) XQuery/JSONiq processor. The following built-in functions are available in every query.

### JSON Utility (`jn:`)

These core JSONiq functions complement the SirixDB-specific `jn:` functions listed above.

| Function | Signature | Description |
|----------|-----------|-------------|
| `jn:keys` | `($objects as item()*)` | Returns distinct field names from one or more JSON objects. |
| `jn:size` | `($array as array?)` | Returns the number of elements in a JSON array. |
| `jn:parse` | `($string as xs:string?)` | Parses a JSON string into a JSON item. |
| `jn:collection` | `()` or `($name)` | Returns the default collection or a named collection. |

```xquery
(: Get all field names of an object :)
jn:keys({"name":"Alice", "age":30})
(: => "name" "age" :)

(: Parse a JSON string :)
let $data := jn:parse('{"x": 42}')
return $data.x
(: => 42 :)
```

### Brackit Extensions (`bit:`)

Utility functions provided by the Brackit engine under the `bit:` namespace (`http://brackit.org/ns/bit`).

| Function | Signature | Description |
|----------|-----------|-------------|
| `bit:len` | `($array as array?)` | Returns the length of an array. |
| `bit:fields` | `($object as object?)` | Returns field names of a JSON object. |
| `bit:values` | `($object as object?)` | Returns all values of a JSON object. |
| `bit:array-values` | `($array as array?)` | Returns all values from an array as a sequence. |
| `bit:parse` | `($string as xs:string?)` | Parses an XML string into a document node. |
| `bit:serialize` | `($items as item()*)` | Serializes items to an XML string. |
| `bit:eval` | `($query as item())` | Dynamically evaluates a query string. |
| `bit:now` | `()` | Returns the current time in milliseconds since epoch. |
| `bit:some` | `($sequence as item()*)` | Returns `true` if any item in the sequence is truthy. |
| `bit:every` | `($sequence as item()*)` | Returns `true` if all items in the sequence are truthy. |
| `bit:create` | `($name as xs:string)` | Creates an empty collection. |
| `bit:drop` | `($name as xs:string)` | Deletes a collection. |
| `bit:exists` | `($name as xs:string)` | Returns `true` if a collection exists. |

```xquery
(: Inspect object structure :)
let $obj := {"name":"Alice", "age":30, "city":"Berlin"}
return {
  "fields": bit:fields($obj),
  "values": bit:values($obj)
}

(: Dynamic evaluation :)
bit:eval("1 + 2")
(: => 3 :)
```

### I/O Functions (`io:`)

File system operations under the `io:` namespace (`http://brackit.org/ns/io`).

| Function | Signature | Description |
|----------|-----------|-------------|
| `io:ls` | `($path)` | Lists all files in a directory. |
| `io:ls` | `($path, $pattern)` | Lists files matching a regex pattern. |
| `io:read` | `($filename)` | Reads entire file content as a string. |
| `io:readline` | `($filename)` | Reads file content line by line. |
| `io:write` | `($filename, $items)` | Writes items to a file. |
| `io:writeline` | `($filename, $items)` | Writes items to a file with newlines. |
