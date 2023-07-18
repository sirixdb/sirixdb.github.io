---
layout: documentation
doctitle: JSONiq-API
title: SirixDB - JSONiq-API
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/jsoniq-api.md)

## Maven Artifacts

First, you have to get the dependency on our Sirix JSONiq/XQuery project. At this stage of development, please use the latest SNAPSHOT artifacts from the OSS snapshot repository. Just add the following repository section to your POM file:

```xml
<repository>
  <id>sonatype-nexus-snapshots</id>
  <name>Sonatype Nexus Snapshots</name>
  <url>https://oss.sonatype.org/content/repositories/snapshots</url>
  <releases>
    <enabled>false</enabled>
  </releases>
  <snapshots>
    <enabled>true</enabled>
  </snapshots>
</repository>
```

Or for Gradle:
```gradle
apply plugin: 'java'
apply plugin: 'maven'

repositories {
    maven {
          url "https://oss.sonatype.org/content/repositories/snapshot"
    }
}
```

Maven artifacts are deployed to the central maven repository once we release a new version (however, please use the SNAPSHOT-versions as of now). Currently, the following artifacts are available. Make sure that snapshots are getting updated with newer versions in your IDE.

Core project:

```xml
<dependency>
  <groupId>io.sirix</groupId>
  <artifactId>sirix-xquery</artifactId>
  <version>0.9.6-SNAPSHOT</version>
</dependency>
```

To add the dependency in Gradle:
```gradle
dependencies {
  compile 'io.sirix:sirix-xquery:0.9.6-SNAPSHOT'
}
```

**You have to use Java 20 and the provided Gradle wrapper**

## Import and Query
First, we might want to import an XML document into Sirix. We'll create a database with the imported XML document as a single resource file with the XQuery function `sdb:load(xs:string, xs:string, xs:string) as node()`. The first argument is the database to create, the second the resource representing the imported XML document, and the third parameter is the resource to import. Then we'll be able to load the resource again and execute our first query (`sdb:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']`):

```java
final var doc = Paths.get("src", "main", "resources", "orga.xml");

// Initialize query context and store.
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var queryLoadIntoSirix = String.format("xml:load('mydoc.col', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(queryLoadIntoSirix);
  new XQuery(queryLoadIntoSirix).evaluate(ctx);

  System.out.println("");
  System.out.println("Query loaded document:");
  final var query = "xml:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']";
  System.out.println(query);
  final var query = new XQuery(compileChain, query);
  query.prettyPrint().serialize(ctx, System.out);

  System.out.println("");
}
```

In the above example we are importing (loading) an XML document from a file into SirixDB. We can import XML documents stored as simple Strings with the store-function:

```xquery
xml:store('mydoc.col', 'mydoc.xml', '<xml>foo<bar/></xml>')
```

Loading a collection of XML files in SirixDB is as simple as using the following query. `dir` is a directory path and we're importing all files with an `.xml` suffix:

```xquery
final var ctx = SirixQueryContext.createWithNodeStore(store);
final var query = String.format("bit:load('mydocs.col', io:ls('%s', '\\.xml$'))", dir);
new XQuery(query).evaluate(ctx);
```

And querying the collection is as simple as using the function collection:

```xquery
for $doc in collection('mydocs.col') return $doc
```

To store JSON data in SirixDB, we can use the store function within another namespace (`jn`):

```java
// Initialize query context and store.
try (final var store = BasicJsonDBStore.newBuilder().build();
    final var ctx = SirixQueryContext.createWithJsonStore(store);
    final var chain = SirixCompileChain.createWithJsonStore(store)) {
  // Use XQuery to store a JSON string into the store.
  System.out.println("Storing document:");
  final var storeQuery = "jn:store('mycol.jn','mydoc.jn','[\"bla\", \"blubb\"]')";
  System.out.println(storeQuery);
  new XQuery(chain, storeQuery).evaluate(ctx);
}
```

We can also store a bunch of JSON strings within several resources in the database (`mycol.jn`):

```xquery
jn:store('mycol.jn',(),('["bla", "blubb"]','{"foo": true}'))
```

In that case, the second parameter, which otherwise denotes the resource name, is not used. Furthermore, in both cases, the database is implicitly created. However, a fourth boolean parameter can be used to add resources. It is `true()` if a new database should be created or `false()` if the resource should be added to an existing database:

```xquery
jn:store('mycol.jn','mydoc.jn','["foo", "bar"]',false())
```

In this case the resource is added to the `mycol.jn` database as `mydoc.jn`.

We can open the stored resources again, either via a jn:collection(...) function to retrieve all resources in a database:

```xquery
for $doc in jn:collection('mydocs.col') return $doc
```

or via `jn:doc(xs:string, xs:string, xs:int) as json-item()`, which is almost identical as the version to open XML resources. The first parameter is the database to open, the second parameter is the resource, and the last parameter is the optional revision to open. Without the last parameter, SirixDB opens the most recent revision.

For instance, if we have stored the following very JSON-string as a resource in SirixDB `{"sirix":{"revisionNumber":1}}`, then we'll be able to retrieve the revision number simply via:

`jn:doc('mycol.jn','mydoc.jn').sirix.revisionNumber`

This example query shows the `deref`-operator `.` which is used to select object values by their key name.

We'll save other JSON examples for later. First, we want to show how to update XML and JSON resources.

### Update a Resource

In order to update a resource, we're able to use XQuery Update statements. First, we load an XML document again into a resource in a (to be created) database. The database is named `mycol.xml`, and the resource `mydoc.xml`. Then we open the database and the resource again. We open the resource in its most recent revision and insert an XML fragment (`<a><b/></a>`) as a first child into the root element log. We serialize the result to `STDOUT` again.

```java
// Prepare sample document.
final var doc = generateSampleDoc("sample");

// Initialize query context and store.
try (final var store = BasicXmlDBStore.newBuilder().build();
    final var ctx = SirixQueryContext.createWithNodeStore(store)) {
  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var xq1 = String.format("xml:load('mycol.xml', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(xq1);
  new XQuery(xq1).evaluate(ctx);

  // Reuse store and query loaded document.
  System.out.println();
  System.out.println("Query loaded document:");
  final var xq2 = "let $doc := xml:doc('mycol.xml', 'mydoc.xml')\n" + "let $log = $doc/log return \n"
    + "( insert nodes <a><b/></a> into $log )\n";
  System.out.println(xq2);
  new XQuery(xq2).execute(ctx);

  final var query = new XQuery("xml:doc('mycol.xml', 'mydoc.xml')");
  query.prettyPrint().serialize(ctx, System.out);
  System.out.println();
}
```
Note that a transaction is auto-committed in this case and that the element nodes `a` and `b` are stored in a new revision. Thus, in this case, we open the most recent revision, which is revision two. After creating and bootstrapping a resource, the revision number is 0 with only a document-root node. Once we commit our imported XML document we have stored a first revision. We're serializing the stored revision in another query to `STDOUT` again.

SirixDB currently doesn't support update expressions for the JSON-XQuery extension. For now, we have to use the transactional cursor-based API to update JSON resources. We can simply open the database with XQuery and get the transactional cursor via the `getTrx()`-method on the result sequence:

```java
final var seq = new XQuery(compileChain, query).execute(ctx);
final var rtx = seq.getTrx();
```

In Java or Kotlin we can use the transaction to insert Object-structures, Arrays, String, Number, Boolean, and Null-values.

For instance, we can insert JSON data as the first children of arrays or as the right siblings of array items:

`JsonNodeTrx insertSubtreeAsFirstChild(JsonReader reader)`

`JsonNodeTrx insertSubtreeAsRightSibling(JsonReader reader)`

If the cursor is located on an object node, we can insert records (key/value pairs):

`JsonNodeTrx insertObjectRecordAsFirstChild(String key, ObjectRecordValue<?> value)`

Object record values can be all JSON node types (`ArrayValue`, `ObjectValue`, `BooleanValue`, `StringValue`, `NumberValue` and `NullValue`). If the cursor is located on an object key, you can insert other JSON records as right siblings:

`JsonNodeTrx insertObjectRecordAsRightSibling(String key, ObjectRecordValue<?> value)`

We can find all possible methods in the interface `org.sirix.api.json.JsonNodeTrx`.

### Temporal axis
SirixDB not only provides all standard XPath axes for the stored XML documents but also temporal XPath axes. We can use these axes to analyze how a resource or a subtree therein has changed between several revisions.

Temporal axes are compatible with node tests:

`<temporalaxis>::<nodetest>` is defined as `<temporalaxis>::*/self::<nodetest>`

For instance, to simply serialize all revisions, we can use the axis `all-times::`

```java
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println();
  System.out.println("Query loaded document:");
  final var queryString = "xml:doc('mycol.xml', 'mydoc.xml')/log/all-times::*";
  System.out.println(queryString);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

SirixDB supports a lot of temporal axes: `first::` to get a node in the first revision, `last::` to get a node in the last revision, `previous::` to get the node in the previous revision, `next::` to get the node in the next revision, `future::` and `future-or-self::` to get a node in all future revisions or the current and future revisions, `past::` and `past-or-self::` to get a node in past revisions or the current and past revisions. We have already seen the `all-times::`-axis, which iterates over a node in all revisions.

JSON instead has no notion of the navigational axis, instead, SirixDB provides custom functions:

- `jn:future($item as json-item(), $includeSelf as xs:boolean) as json-item()*`: Function for selecting a json-item in the future or the future-or-self. The first parameter is the context item. The second parameter denotes if the current item should be included in the result or not.

- `jn:past($item as json-item(), $includeSelf as xs:boolean) as json-item()*`: Function for selecting a json-item in the past or the past-or-self. The first parameter is the context item. The second parameter denotes if the current item should be included in the result or not.

- `jn:all-times($item as json-item()) as json-item()+`: Function for selecting a json-item in all revisions.

- `jn:first($item as json-item()) as json-item()?`: Function for selecting a json-item in the first revision.

- `jn:last($item as json-item()) as json-item()?`: Function for selecting a json-item in the last / most-recent revision.

- `jn:previous($item as json-item()) as json-item()?`: Function for selecting a json-item in the previous revision.

- `jn:next($item as json-item()) as json-item()?`: Function for selecting a json-item in the next revision.

### Open a Specific Revision
Once we've stored a few revisions of a resource in SirixDB we might want to open a specific revision again. We can use the `doc` function again, but this time with a third parameter:

`xml:doc('mycol.xml', 'mydoc.xml', 1)`

SirixDB opens the database `mycol.xml` and the resource `mydoc.xml` in revision one. Without the additional revision-number parameter SirixDB would have opened the most recent revision.

However, we might also want to load a revision by a given point in time. We're able to use the function `sdb:open($database as xs:string, $resource as xs:string, $pointInTime as xs:dateTime) as $doc`:

```java
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println();
  System.out.println("Query loaded document:");
  final var queryString = "xml:open('mycol.xml', 'mydoc.xml', xs:dateTime(\"2019-04-01T05:00:00-00:00\"))/log";
  System.out.println(xq3);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```
We open the resource in the database as it looked like on 2019-04-01 05:00:00. 

With the function `open-revisions` we're able to load all revisions of a resource between two points in time:

`xml:open-revisions($database as xs:string, $resource as xs:string, $startDateTime as xs:dateTime, $endDateTime as xs:dateTime) as node()*`

For instance we can use the following Java code:

```java
try (final var store = BasicDBStore.newBuilder().build()
    final var ctx = SirixQueryContext.createWithNodeStore(store);
    final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Query loaded document:");
  final var queryString = "xml:open('mycol.xml', 'mydoc.xml', xs:dateTime(\"2018-04-01T05:00:00-00:00\"), xs:dateTime(\"2019-04-01T05:00:00-00:00\"))";
  System.out.println(queryString);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

### Transactional-Cursor-Based Functions
SirixDB also provides a few functions, which are based on the fact that currently when importing data with XQuery we generate hashes for each node as well as the number of descendants. Furthermore, we always store the number of children of each node. You can use the function

```xquery
sdb:descendant-count($item as structured-item()) as xs:long
```

to retrieve the number of descendants of an item,

```xquery
sdb:child-count($item as structured-item()) as xs:int
```

to retrieve the number of children of an item and

```xquery
sdb:hash($item as structured-item()) as xs:string
```

to retrieve the stored hash of a node.

With the function

```xquery
xml:attribute-count($node as structured-item()) as xs:int
```

you'll get the number of attributes of a node (an element node).

You can get the most recent revision number with the function

```xquery
sdb:most-recent-revision($item as structured-item()) as xs:int
```

You can get the unique, stable key/ID of an item with

```xquery
sdb:nodekey($item as structured-item()) as xs:long
```

To commit a transaction if no auto-commit is enabled

```xquery
sdb:commit($item as structured-item()) as xs:node
```

To rollback a transaction (result item is the aborted revision number)

```xquery
sdb:rollback($item as structured-item()) as xs:int
```

To get the revision timestamp of a node (the timestamp when the transaction has been committed)

```xquery
sdb:timestamp($item as structured-item()) as xs:dateTime
```

To select a specific item

```xquery
sdb:select-item($node as xs:structured-item, $nodeKey as xs:integer) as xs:structured-item
```

To get the item history:

```xquery
sdb:item-history($item as xs:structured-item) as xs:structured-item+
```

## JSON Extension (Beta)

We copied the description if the JSON extension in Brackit, the XQuery compiler we are using:

Brackit features a seamless integration of JSON-like objects and arrays directly at the language level.

You can easily mix arbitrary XML and JSON data in a single query or simply use brackit to convert data from one format into the other. This allows you to get the most out of your data.

The language extension allows you to construct and operate JSON data directly; additional utility functions help you to perform typical tasks.

Everything is designed to simplify joint processing of XDM and JSON and to maximize the freedom of developers. Thus, our extension effectively supports some sort of superset of XDM and JSON. That means, it is possible to create arrays and objects which do not strictly conform to the JSON RFC. It's up to you to decide how you want to have your data look like!

### Arrays

Arrays can be created using an extended version of the standard JSON array syntax:

```xquery
(: statically create an array with 3 elements of different types: 1, 2.0, "3" :)
[ 1, 2.0, "3" ]

(: for compliance with the JSON syntax the tokens 'true', 'false', and 'null'
   are translated into the XML values xs:bool('true'), xs:bool('false') and empty-sequence()
:)
[ true, false, jn:null() ]

(: is different to :)
[ (true), (false), (null) ]
(: where each field is initialized as the result of a path expression
   starting from the current context item, e,g., './true'
:)

(: dynamically create an array by evaluating some expressions: :)
[ 1+1, substring("banana", 3, 5), () ] (: yields the array [ 2, "nana", () ] :)

(: arrays can be nested and fields can be arbitrary sequences :)
[ (1 to 5) ] (: yields an array of length 1: [(1,2,3,4,5)] :)
[ some text ] (: yields an array of length 1 with an XML fragment as field value :)
[ 'x', [ 'y' ], 'z' ] (: yields an array of length 3: [ 'x' , ['y'], 'z' ] :)

(: a preceding '=' distributes the items of a sequence to individual array positions :)
[ =(1 to 5) ] (: yields an array of length 5: [ 1, 2, 3, 4, 5 ] :)

(: array fields can be accessed by the '[[ ]]' postfix operator: :)
let $a := [ "Jim", "John", "Joe" ] return $a[[1]] (: yields the string "John" :)

(: the function bit:len() returns the length of an array :)
bit:len([ 1, 2, ]) (: yields 2 :)
```

### Objects

Objects provide an alternative to XML to represent structured data. Like with arrays, we support an extended version of the standard JSON object syntax:

```xquery
(: statically create a record with three fields named 'a', 'b' and 'c' :)
{ "a": 1, "b": 2, "c": 3 }

(: for compliance with the JSON syntax the tokens 'true', 'false', and 'null'
   are translated into the XML values xs:bool('true'), xs:bool('false') and a new atomic null type
:)
{ "a": true "b": false, "c": jn:null()}

(: field names are modeled as xs:QName and may be set in double quotes or 
   single quotes.
:)
{ 'b': 2, "c": 3 }

(: field values may be arbitrary expressions:)
{ "a": concat('f', 'oo'), 'b': 1+1, "c": [1,2,3] } (: yields {"a": "foo", "b": 2, "c": [1,2,3]} :)

(: field values are defined by key-value pairs or by an expression
   that evaluates to a record
:)
let $r := { "x":1, "y":2 } return { $r, "z":3} (: yields {"x": 1, "y": 2, "z": 3} :)

(: fields may be selectively projected into a new record :)
{"x": 1, "y": 2, "z": 3}{z,y} (: yields {"z": 3, "y": 2} :)

(: values of record field can be accessed using the deref operator '=>' :)
{ "a": "hello", "b": "world" }.b (: yields the string "world" :)

(: the deref operator can be used to navigate into deeply nested record structures :)
let $n := yval let $r := {"e": {"m":'mvalue', "n":$n}} return $r.e.n/y (: yields the XML fragment yval :)

(: the function bit:fields() returns the field names of a record :)
let $r := {"x": 1, "y": 2, "z": 3} return bit:fields($r) (: yields the xs:QName array [ x, y, z ] :)

(: the function bit:values() returns the field values of a record :)
let $r := {"x": 1, "y": 2, "z": (3, 4) } return bit:values($r) (: yields the array [ 1, 2, (2,4) ] :)
```

### Parsing JSON

```xml
(: the utility function json:parse() can be used to parse JSON data dynamically
   from a given xs:string
:)
let $s := io:read('/data/sample.json') return json:parse($s)
```

### Index structures
Index structures in Sirix are always user-defined, typed indexes. We provide three types of indexes, name indexes on elements (either attribute nodes in XML/XDM resources, or name indexes on JSON object record keys) path indexes, or so-called content-and-structure (CAS)-indexes which are a kind of value on specific paths.

First, we create an element index on elements with the local name `src`:

```java
// Create and commit name index on all elements with QName 'src'.
try (final var store = BasicXmlDBStore.newBuilder().build()
  final var ctx = SirixQueryContext.createWithNodeStoreAndCommitStrategy(store, CommitStrategy.EXPLICIT);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Create name index for all elements with name 'src':");
  final var query = new XQuery(compileChain,
        "let $doc := xml:doc('mydocs.col', 'resource1') "
            + "let $stats := xml:create-name-index($doc, fn:QName((), 'src')) "
            + "return <rev>{xml:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("Name index creation done.");
}
```

And in order to query the name index again sometime later:

```java
// Query name index.
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Query name index (src-element).");
 
  final var queryString = "let $doc := xml:doc('mydocs.col', 'resource1')"
      + " let $sequence := xml:scan-name-index($doc, xml:find-name-index($doc, fn:QName((), 'src')), fn:QName((), 'src'))"
      + " return sdb:sort($sequence)";
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint();
  query.serialize(ctx, System.out);
}
```

In order to create a path index on all paths in the resource we can use:

```java
// Create and commit path index on all elements.
try (final var store = BasicXmlDBStore.newBuilder().build();
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Create path index for all elements (all paths):");
  final var query =
      new XQuery(compileChain, "let $doc := xml:doc('mydocs.col', 'resource1') "
          + "let $stats := xml:create-path-index($doc, '//*') " + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("Path index creation done.");
}
```

And in order to query the path index again sometime later:

```java
// Query path index which are children of the log-element (only elements).
try (final var store = BasicXmlDBStore.newBuilder().build();
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Find path index for all elements which are children of the log-element (only elements).");
  
  final var node = (DBNode) new XQuery(new SirixCompileChain(store), "doc('mydocs.col')").execute(ctx);

  // We can simply use sdb:find-path-index('xs:node', 'xs:string') to find the appropriate index number and then scan the index.
  final var query = "let $doc := xml:doc('mydocs.col', 'resource1') " + "return sdb:sort(xml:scan-path-index($doc, "
      + "xml:find-path-index($doc, '//log/*'), '//log/*'))";
  final var sortedSeq = new XQuery(compileChain, query).execute(ctx);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

Note that in this example we showed how to get access to the low-level transactional cursor API of Sirix and use this API.

In order to create a CAS index for all attributes, another one for text-nodes and a third one for all integers text-nodes:

```java
// Create and commit CAS indexes on all attribute- and text nodes.
try (final var store = BasicXmlDBStore.newBuilder().build()
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println(
      "Create a CAS index for all attributes and another one for text nodes. A third one is created for all integers:");
  final var query = new XQuery(compileChain,
      "let $doc := xml:doc('mydocs.col', 'resource1') "
          + "let $casStats1 := xml:create-cas-index($doc, 'xs:string', '//@*') "
          + "let $casStats2 := xml:create-cas-index($doc, 'xs:string', '//*') "
          + "let $casStats3 := xml:create-cas-index($doc, 'xs:integer', '//*') "
          + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("CAS index creation done.");
}
```

And to find and query the CAS index (for all attribute values) again:

```java
// Query CAS index.
try (final var store = BasicXmlDBStore.newBuilder().build();
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Find CAS index for all attribute values.");
  
  final var sortedSeq =
      "let $doc := xml:doc('mydocs.col', 'resource1') return sdb:sort(sdb:scan-cas-index($doc, sdb:find-cas-index($doc, 'xs:string', '//@*'), 'bar', true(), true(), '==', ()))";
  final var sortedSeq = new XQuery(compileChain, query).execute(ctx);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (final var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

In general, for each index type, we have a function to create the index, to find the index number for a given query again (the index definition must match), and to query the index.
