---
layout: documentation
doctitle: JSONiq API
title: SirixDB - JSONiq API
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/jsoniq-api.md)

SirixDB uses [JSONiq](https://www.jsoniq.org/) — the JSON query language — as its primary API for storing, querying, and updating JSON data. JSONiq extends XQuery with native JSON support, making it ideal for working with SirixDB's temporal document store.

For a complete list of all available functions, see the [Function Reference](/docs/jsoniq-functions.html).

## Setup

Add the SirixDB query module to your project.

**Maven:**

```xml
<dependency>
  <groupId>io.sirix</groupId>
  <artifactId>sirix-query</artifactId>
  <version>0.10.1-SNAPSHOT</version>
</dependency>
```

**Gradle:**

```gradle
dependencies {
  implementation 'io.sirix:sirix-query:0.10.1-SNAPSHOT'
}
```

For snapshot versions, add the Sonatype snapshot repository:

```xml
<repository>
  <id>sonatype-nexus-snapshots</id>
  <url>https://oss.sonatype.org/content/repositories/snapshots</url>
  <snapshots><enabled>true</enabled></snapshots>
</repository>
```

**Requires Java 25 and the provided Gradle wrapper.**

## Running Queries from Java

All JSONiq queries run through the `Query` class with a JSON-specific store and context:

```java
try (final var store = BasicJsonDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithJsonStore(store);
     final var chain = SirixCompileChain.createWithJsonStore(store)) {

  // Store JSON data
  new Query(chain, "jn:store('mydb', 'products', '[{\"name\":\"Laptop\",\"price\":999}]')")
      .evaluate(ctx);

  // Query and print results
  final var query = new Query(chain, "jn:doc('mydb', 'products')[0].name");
  query.serialize(ctx, System.out);
  // => "Laptop"
}
```

## Storing Data

Use `jn:store` to create a database and store JSON data. The database is created automatically if it doesn't exist.

```xquery
(: Store a JSON array as a named resource :)
jn:store('shop', 'products', '[{"name":"Laptop","price":999},{"name":"Phone","price":699}]')

(: Store from a file :)
jn:load('shop', 'inventory', '/path/to/data.json')

(: Add another resource to an existing database :)
jn:store('shop', 'customers', '[{"name":"Alice"}]', false())
```

## Opening and Querying Data

Open a resource with `jn:doc` and navigate using JSONiq's dot notation and array indexing:

```xquery
(: Open the most recent revision :)
let $doc := jn:doc('shop', 'products')
return $doc[0].name
(: => "Laptop" :)

(: Open a specific revision :)
jn:doc('shop', 'products', 1)

(: Open at a point in time :)
jn:open('shop', 'products', xs:dateTime('2024-06-15T10:00:00Z'))

(: Query all resources in a database :)
for $doc in jn:collection('shop')
return $doc
```

Array elements are accessed with `[]` using zero-based indexing. Object fields are accessed with the `.` (deref) operator:

```xquery
let $doc := jn:doc('shop', 'products')
return {
  "first-product": $doc[0].name,
  "second-price": $doc[1].price,
  "count": jn:size($doc)
}
```

## Updating Data

SirixDB supports all JSONiq update expressions. Each update automatically creates a new revision.

```xquery
(: Replace a value :)
let $doc := jn:doc('shop', 'products')
return replace json value of $doc[0].price with 899

(: Append to an array :)
let $doc := jn:doc('shop', 'products')
return append json {"name":"Tablet","price":449} into $doc

(: Insert a field into an object :)
let $doc := jn:doc('shop', 'products')
return insert json {"stock": 50} into $doc[0]

(: Delete an array element :)
let $doc := jn:doc('shop', 'products')
return delete json $doc[1]

(: Rename a field :)
let $doc := jn:doc('shop', 'products')
return rename json $doc[0].price as "cost"

(: Insert at a specific array position :)
let $arr := jn:doc('shop', 'products')
return insert json {"name":"Monitor","price":349} into $arr at position 1
```

You can also commit with a message or rollback changes:

```xquery
let $doc := jn:doc('shop', 'products')
return (
  replace json value of $doc[0].price with 799,
  sdb:commit($doc, "Summer sale pricing")
)
```

## Temporal Queries

SirixDB's key feature is temporal querying — every update creates an immutable revision, and you can navigate the full history.

### Navigating Revisions

```xquery
(: See a document across all revisions :)
for $v in jn:all-times(jn:doc('shop', 'products'))
return {"rev": sdb:revision($v), "data": $v}

(: Step forward and backward :)
let $doc := jn:doc('shop', 'products')
return {
  "current-rev": sdb:revision($doc),
  "previous-rev": sdb:revision(jn:previous($doc)),
  "first-rev": sdb:revision(jn:first($doc))
}

(: Get all future versions from revision 2 :)
for $v in jn:future(jn:doc('shop', 'products', 2), true())
return sdb:revision($v)
```

### Tracking Individual Nodes

Every node in SirixDB has a stable, unique key. You can track how individual values change across revisions:

```xquery
(: Find a node's key :)
let $doc := jn:doc('shop', 'products')
return sdb:nodekey($doc[0].price)

(: Track a specific node's history :)
let $item := sdb:select-item(jn:doc('shop', 'products'), 6)
for $v in sdb:item-history($item)
return {"rev": sdb:revision($v), "value": $v}
```

### Comparing Revisions

Use `jn:diff` to compute structural differences between any two revisions:

```xquery
jn:diff('shop', 'products', 1, 4)
(: Returns a JSON object describing inserts, deletes, updates, and replacements :)
```

### Bitemporal Queries

For resources configured with valid-time support, query along two time axes — system time (when recorded) and valid time (when true in the real world):

```xquery
(: What did we know on March 5 about data valid on February 1? :)
jn:open-bitemporal('customers', 'addresses',
  xs:dateTime('2024-02-01T00:00:00Z'),
  xs:dateTime('2024-03-05T00:00:00Z'))
```

## Node Metadata

Inspect metadata about any node using `sdb:` functions:

```xquery
let $doc := jn:doc('shop', 'products')
return {
  "revision": sdb:revision($doc),
  "timestamp": sdb:timestamp($doc),
  "children": sdb:child-count($doc),
  "descendants": sdb:descendant-count($doc),
  "nodekey": sdb:nodekey($doc),
  "hash": sdb:hash($doc),
  "path": sdb:path($doc[0].name)
}
```

## Indexes

SirixDB supports three index types for faster lookups: **name** (field names), **path** (document paths), and **CAS** (content-and-structure, for typed value queries).

```xquery
(: Create a CAS index on the "price" path for numeric lookups :)
let $doc := jn:doc('shop', 'products')
return jn:create-cas-index($doc, 'xs:decimal', '/[]/price')

(: Query the index for prices between 0 and 500 :)
let $doc := jn:doc('shop', 'products')
let $idx := jn:find-cas-index($doc, 'xs:decimal', '/[]/price')
return jn:scan-cas-index-range($doc, $idx, 0, 500, true(), true(), 'xs:decimal')

(: Create a name index on specific fields :)
let $doc := jn:doc('shop', 'products')
return jn:create-name-index($doc, ('name', 'price'))

(: Create a path index on all paths :)
let $doc := jn:doc('shop', 'products')
return jn:create-path-index($doc)
```

See the [Function Reference](/docs/jsoniq-functions.html#indexes) for the complete index API.

## JSONiq Language Basics

JSONiq extends XQuery with native JSON support. Here are the key language features.

### Arrays

```xquery
(: Create arrays :)
let $a := [1, 2.0, "three", true, false, jn:null()]
return $a[0]
(: => 1 :)

(: Distribute sequence items into array positions with '=' :)
[=(1 to 5)]
(: => [1, 2, 3, 4, 5] :)

(: Without '=', the sequence stays as one element :)
[(1 to 5)]
(: => [(1,2,3,4,5)] :)

(: Get array length :)
bit:len([1, 2, 3])
(: => 3 :)
```

### Objects

```xquery
(: Create objects :)
let $obj := {"name": "Alice", "age": 30, "scores": [95, 87, 92]}
return $obj.name
(: => "Alice" :)

(: Merge objects :)
let $base := {"x": 1, "y": 2}
return {$base, "z": 3}
(: => {"x": 1, "y": 2, "z": 3} :)

(: Project specific fields :)
{"x": 1, "y": 2, "z": 3}{x, z}
(: => {"x": 1, "z": 3} :)

(: Inspect object structure :)
let $obj := {"a": 1, "b": 2}
return bit:fields($obj)
(: => ["a", "b"] :)
```

### Parsing JSON

```xquery
let $s := io:read('/data/sample.json')
return jn:parse($s)
```
