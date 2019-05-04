---
layout: documentation
doctitle: XQuery-API
---

### Maven artifacts

First, you have to get the dependeny on our Sirix XQuery project. At this stage of development please use the latest SNAPSHOT artifacts from the OSS snapshot repository. Just add the following repository section to your POM file:

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

However, if you prefer, we just released version 0.9.1 of Sirix in Maven Central.

Maven artifacts are deployed to the central maven repository (however please use the SNAPSHOT-variants as of now). Currently the following artifacts are available. Make sure that snapshots are getting updated with newer versions in your IDE.

Core project:

```xml
<dependency>
  <groupId>io.sirix</groupId>
  <artifactId>sirix-xquery</artifactId>
  <version>0.9.1-SNAPSHOT</version>
</dependency>
```

To add the dependency in Gradle:
```gradle
dependencies {
  compile 'io.sirix:sirix-xquery:0.9.1-SNAPSHOT'
}
```

### Import and query
First, you might want to import an XML-document into Sirix and create a first database with the shredded/imported XML-document as a single resource file with the XQuery function `sdb:load(xs:string, xs:string, xs:string) as node()`. The first argument is the database to create, the second the resource which represents the imported XML-document and the third parameter is the resource to import. Then loading the resource again and execute your first query (`sdb:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']`):

```java
final var doc = Paths.get("src", "main", "resources", "orga.xml");

// Initialize query context and store.
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var queryLoadIntoSirix = String.format("sdb:load('mydoc.col', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(queryLoadIntoSirix);
  new XQuery(queryLoadIntoSirix).evaluate(ctx);

  System.out.println("");
  System.out.println("Query loaded document:");
  final var query = "sdb:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']";
  System.out.println(query);
  final var query = new XQuery(compileChain, query);
  query.prettyPrint().serialize(ctx, System.out);

  System.out.println("");
}
```

In the above example you are loading an XML-document from a file into Sirix. You can do the same with XML-documents stored as simple Strings with the store-function:

```java
final var ctx = SirixQueryContext.createWithNodeStore(store);
final var query = "sdb:store('mydoc.col', 'mydoc.xml', '<xml>foo<bar/></xml>')";
new XQuery(query).evaluate(ctx);
```

Loading a collection of XML files in Sirix is as simple as using the following query for instance (dir is a directory path and you're importing all files with an `.xml` suffix):

```java
final var ctx = SirixQueryContext.createWithNodeStore(store);
final var query = String.format("bit:load('mydocs.col', io:ls('%s', '\\.xml$'))", dir);
new XQuery(query).evaluate(ctx);
```

And querying the collection is as simple as using the function collection:

```java
final var ctx = SirixQueryContext.createWithNodeStore(store);
final var query = "for $doc in collection('mydocs.col') return $doc";
new XQuery(query).prettyPrint().serialize(ctx, System.out);
```

In order to store JSON-documents into Sirix the store-function within another namespace (`js`) is used:

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

For sure you can also store a bunch of JSON-strings within several resources in the database (`mycol.jn`):

```java
try (final var store = BasicJsonDBStore.newBuilder().build();
    final var ctx = SirixQueryContext.createWithJsonStore(store);
    final var chain = SirixCompileChain.createWithJsonStore(store)) {
  // Use XQuery to store multiple JSON strings into the store.
  System.out.println("Storing strings:");
  final var query = "jn:store('mycol.jn',(),('[\"bla\", \"blubb\"]','{\"foo\": true}'))";
  System.out.println(query);
  new XQuery(chain, query).evaluate(ctx);
}
```

In that case the second parameter, which otherwise denotes the resource-name is not used. Furthermore in both cases the database is implicitly created. However a fourth boolean parameter (`true()` if a new database should be created or `false()` if the resource should simply be added to an existing database) can be used to simply add resources like this:

```java
try (final var store = BasicJsonDBStore.newBuilder().build();
    final var ctx = SirixQueryContext.createWithJsonStore(store);
    final var chain = SirixCompileChain.createWithJsonStore(store)) {
  // Use XQuery to add a JSON string to the collection.
  System.out.println("Storing strings:");
  final var queryAdd = "jn:store('mycol.jn','mydoc.jn','[\"foo\", \"bar\"]',false())";
  System.out.println(queryAdd);
  new XQuery(chain, queryAdd).evaluate(ctx);
}
```

In this case the resource is simply added to the `mycol.jn` database as `mydoc.jn`.

You can open the stored resources again, either via a jn:collection(...) function to retrieve all resources in a database:

```java
final var ctx = SirixQueryContext.createWithNodeStore(store);
final var query = "for $doc in jn:collection('mydocs.col') return $doc";
new XQuery(query).prettyPrint().serialize(ctx, System.out);
```

or via `jn:doc(xs:string, xs:string, xs:int) as json-item()`, which is almost identical as the version to open XML-resources. The first parameter is the database to open, the second parameter the resource and the last one is the optional revision to open (without the last parameter it opens the most recent revision).

For instance if we have stored the following very simple JSON-string as a resource in Sirix `{"sirix":{"revisionNumber":1}}`, then you can retrieve the revisionNumber simply via:

`jn:doc('mycol.jn','mydoc.jn')=>sirix=>revisionNumber`

This shows the `deref`-operator `=>` which is used to select object/record values by their key name.

We'll save other JSON-stuff for later on. But first we want to show how to update XML- and JSON-resources.

### Update the resource

In order to update a resource you're able to use XQuery Update statements. First we load an XML-document again into a `database/resource` whereas the database is named `mycol.xml` and the resource `mydoc.xml`. Then we open the database/resource again in their most recent revision and insert an XML fragment (`<a><b/></a>`) as a first child into the root element log. The result is serialized to `STDOUT` again.

```java
// Prepare sample document.
final var doc = generateSampleDoc("sample");

// Initialize query context and store.
try (final var store = BasicXmlDBStore.newBuilder().build();
    final var ctx = SirixQueryContext.createWithNodeStore(store)) {
  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var xq1 = String.format("sdb:load('mycol.xml', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(xq1);
  new XQuery(xq1).evaluate(ctx);

  // Reuse store and query loaded document.
  System.out.println();
  System.out.println("Query loaded document:");
  final var xq2 = "let $doc := sdb:doc('mycol.xml', 'mydoc.xml')\n" + "let $log = $doc/log return \n"
    + "( insert nodes <a><b/></a> into $log )\n";
  System.out.println(xq2);
  new XQuery(xq2).execute(ctx);

  final var query = new XQuery("sdb:doc('mycol.xml', 'mydoc.xml')");
  query.prettyPrint().serialize(ctx, System.out);
  System.out.println();
}
```
Note, that a transaction is auto-commited in this case and that the element nodes `a` and `b` are stored in a new revision. Thus, in this case we open the most recent revision, which is revision two (bootstrapped revision is 0 with only a document-root node and revision 1 was the initially imported XML-document) and serialize it to `System.out`.

Regarding JSON we're currently working on update expressions for our XQuery extension (mainly JSONiq). For now you have to use our transactional cursor based API to update JSON-resources. You could for instance simply open the database with XQuery and get the transactional cursor via the `getTrx()`-method on the result sequence:

```java
final var seq = new XQuery(compileChain, query).execute(ctx);
final var rtx = seq.getTrx();
```

In Java or Kotlin we can simply use the transaction to insert whole Object-structures, Arrays, String, Number, Boolean and Null-values.

For instance you can simply insert whole JSON-structures as first childs of arrays or as right siblings of array items for instance like this:

`JsonNodeTrx insertSubtreeAsFirstChild(JsonReader reader)`

`JsonNodeTrx insertSubtreeAsRightSibling(JsonReader reader)`

If the cursor is located on an object node we can insert records (key/value pairs) like this:

`JsonNodeTrx insertObjectRecordAsFirstChild(String key, ObjectRecordValue<?> value)`

Object record values can be all JSON node types (`ArrayValue`, `ObjectValue`, `BooleanValue`, `StringValue`, `NumberValue` and `NullValue`). If the cursor is located on an object key you can insert other JSON records as right siblings:

`JsonNodeTrx insertObjectRecordAsRightSibling(String key, ObjectRecordValue<?> value)`

All possible methods can be found in the interface `org.sirix.api.json.JsonNodeTrx`.

### Temporal axis
We not only provide all standard XPath axis for the XML-documents stored in Sirix, but also temporal XPath axis, which can be used to analyse how a resource or a subtree therein has changed between several revisions.

Temporal axis are compatible with node tests:

`<temporalaxis>::<nodetest>` is defined as `<temporalaxis>::*/self::<nodetest>`

For instance to simply serialize all revisions, we can use the axis `all-time::`

```java
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println();
  System.out.println("Query loaded document:");
  final var queryString = "sdb:doc('mycol.xml', 'mydoc.xml')/log/all-time::*";
  System.out.println(queryString);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

We support a whole bunch of temporal axis: `first::` to get a node in the first revision, `last::` to get a node in the last revision, `previous::` to get the node in the previous revision, `next::` to get the node in the next revision, `future::` and `future-or-self::` to get a node in all future revisions or the current and future revisions, `past::` and `past-or-self::` to get a node in past revisions or the current and past revisions. We have already seen the `all-time::`-axis which iterates over a node in all revisions.

JSON instead has no notion of navigational axis, instead we provide custom functions:

- `jn:future($item as json-item(), $includeSelf as xs:boolean) as json-item()*`: Function for selecting a json-item in the future or the future-or-self. The first parameter is the context item. Second parameter is if the current item should be included in the result or not.

- `jn:past($item as json-item(), $includeSelf as xs:boolean) as json-item()*`: Function for selecting a json-item in the past or the past-or-self. The first parameter is the context item. Second parameter is if the current item should be included in the result or not.

- `jn:all-times($item as json-item()) as json-item()+`: Function for selecting a json-item in all revisions.

- `jn:first($item as json-item()) as json-item()?`: Function for selecting a json-item in the first revision.

- `jn:last($item as json-item()) as json-item()?`: Function for selecting a json-item in the last / most-recent revision.

- `jn:previous($item as json-item()) as json-item()?`: Function for selecting a json-item in the previous revision.

- `jn:next($item as json-item()) as json-item()?`: Function for selecting a json-item in the next revision.

### Open a specific revision
Once you've stored a few revisions of a resource in Sirix you might want to open a specific revision again. This can simply be done by using a third parameter to the doc-function in the sirix-namespace For instance using 

`sdb:doc('mycol.xml', 'mydoc.xml', 1)`

This opens the database `mycol.xml` and the resource `mydoc.xml` in revision one. Without the additional revision-number parameter the most recent revision is going to be opened.

However, you might also be interested in loading a revision by a given timestamp/point in time. You might simply use the function `sdb:open($database as xs:string, $resource as xs:string, $pointInTime as xs:dateTime) as $doc`.

```java
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println();
  System.out.println("Query loaded document:");
  final var queryString = "sdb:open('mycol.xml', 'mydoc.xml', xs:dateTime(\"2019-04-01T05:00:00-00:00\"))/log";
  System.out.println(xq3);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

with the following function you're able to load the database/resource how it looked like between two revisions. Sirix searches for the closest revisions to the given timestamps. The function returns the document node in all revisions, which have been committed in-between.

`sdb:open-revisions($database as xs:string, $resource as xs:string, $startDateTime as xs:dateTime, $endDateTime as xs:dateTime) as node()*`

A simple example is

```java
try (final var store = BasicDBStore.newBuilder().build()
    final var ctx = SirixQueryContext.createWithNodeStore(store);
    final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Query loaded document:");
  final var queryString = "sdb:open('mycol.xml', 'mydoc.xml', xs:dateTime(\"2018-04-01T05:00:00-00:00\"), xs:dateTime(\"2019-04-01T05:00:00-00:00\"))";
  System.out.println(queryString);
  final var query = new XQuery(compileChain, queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

### Transactional cursor based functions
We also provide a few functions, which are based on the fact that currently when importing data with XQuery we generate hashes for each node as well as the number of descendants. Furthermore we always store the number of children of each node. You can use the function

`sdb:descendant-count($node as structured-item()) as xs:long`

to retrieve the number of descendants of a node,

`sdb:child-count($node as structured-item()) as xs:int`

to retrieve the number of children of a node and

`sdb:hash($node as structured-item()) as xs:string`

to retrieve the stored hash of a node.

With the function

`sdb:attribute-count($node as structured-item()) as xs:int`

you'll get the number of attributes of a node (an element node).

You can get the most recent revision number with the function

`sdb:most-recent-revision($node as structured-item()) as xs:int`

The unique, stable key/ID of a node with

`sdb:nodekey($node as structured-item()) as xs:long`

To commit a transaction if no auto-commit is enabled

`sdb:commit($node as structured-item()) as xs:node`

To rollback a transaction (result item is the aborted revision number)

`sdb:rollback($node as structured-item()) as xs:int`

To get the revision timestamp of a node (the timestamp when the transaction has been committed)

`sdb:timestamp($node as structured-item()) as xs:dateTime`

## JSON Extension (Beta)

We copied the description if the JSON extension in Brackit, the XQuery compiler we are using:

Brackit features a seamless integration of JSON-like objects and arrays directly at the language level.

You can easily mix arbitrary XML and JSON data in a single query or simply use brackit to convert data from one format into the other. This allows you to get the most out of your data.

The language extension allows you to construct and operate JSON data directly; additional utility functions help you to perform typical tasks.

Everything is designed to simplify joint processing of XDM and JSON and to maximize the freedom of developers. Thus, our extension effectively supports some sort of superset of XDM and JSON. That means, it is possible to create arrays and objects which do not strictly conform to the JSON RFC. It's up to you to decide how you want to have your data look like!

### Arrays

Arrays can be created using an extended version of the standard JSON array syntax:

```xml
(: statically create an array with 3 elements of different types: 1, 2.0, "3" :)
[ 1, 2.0, "3" ]

(: for compliance with the JSON syntax the tokens 'true', 'false', and 'null'
   are translated into the XML values xs:bool('true'), xs:bool('false') and empty-sequence()
:)
[ true, false, null ]

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

### Records

Records provide an alternative to XML to represent structured data. Like with arrays we support an extended version of the standard JSON object syntax:

```xml
(: statically create a record with three fields named 'a', 'b' and 'c' :)
{ "a": 1, "b": 2, "c": 3 }

(: for compliance with the JSON syntax the tokens 'true', 'false', and 'null'
   are translated into the XML values xs:bool('true'), xs:bool('false') and empty-sequence()
:)
{ "a": true, "b": false, "c": null}

(: field names are modelled as xs:QName and may be set in double quotes,
   single quotes or completely without quotes.
:)
{ a: 1, 'b' : 2, "c": 3 }

(: field values may be arbitrary expressions:)
{ a : concat('f', 'oo') , 'b' : 1+1, c : [1,2,3] } (: yields {a : "foo", b : 2, c : [1,2,3]} :)

(: field values are defined by key-value pairs or by an expression
   that evaluates to a record
:)
let $r := { x:1, y:2 } return { $r, z:3} (: yields {x: 1, y: 2, z: 3} :)

(: fields may be selectively projected into a new record :)
{x: 1, y: 2, z: 3}{z,y} (: yields {z: 3, y: 2} :)

(: values of record field can be accessed using the deref operator '=>' :)
{ a: "hello" , b: "world" }=>b (: yields the string "world" :)

(: the deref operator can be used to navigate into deeply nested record structures :)
let $n := yval let $r := {e : {m:'mvalue', n:$n}} return $r=>e=>n/y (: yields the XML fragment yval :)

(: the function bit:fields() returns the field names of a record :)
let $r := {x: 1, y: 2, z: 3} return bit:fields($r) (: yields the xs:QName array [ x, y, z ] :)

(: the function bit:values() returns the field values of a record :)
let $r := {x: 1, y: 2, z: (3, 4) } return bit:values($r) (: yields the array [ 1, 2, (2,4) ] :)
```

### Parsing JSON

```xml
(: the utility function json:parse() can be used to parse JSON data dynamically
   from a given xs:string
:)
let $s := io:read('/data/sample.json') return json:parse($s)
```

### Index structures
Index structures in Sirix are always user defined, typed indexes. We provide three types of indexes, name indexes on alement- or attribute-nodes in XML/XDM resources or name indexes on JSON object record keys, path indexes and so called content-and-structure (CAS)-indexes which are a kind of value on specific paths.

First, we create an element index on elements with the local name `src`:

```java
// Create and commit name index on all elements with QName 'src'.
try (final var store = BasicXmlDBStore.newBuilder().build()
  final var ctx = SirixQueryContext.createWithNodeStoreAndCommitStrategy(store, CommitStrategy.EXPLICIT);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Create name index for all elements with name 'src':");
  final var query = new XQuery(compileChain,
        "let $doc := sdb:doc('mydocs.col', 'resource1') "
            + "let $stats := sdb:create-name-index($doc, fn:QName((), 'src')) "
            + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("Name index creation done.");
}
```

And in order to query the name index again some time later:

```java
// Query name index.
try (final var store = BasicXmlDBStore.newBuilder().build();
     final var ctx = SirixQueryContext.createWithNodeStore(store);
     final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Query name index (src-element).");
 
  final var queryString = "let $doc := sdb:doc('mydocs.col', 'resource1')"
      + " let $sequence := sdb:scan-name-index($doc, sdb:find-name-index($doc, fn:QName((), 'src')), fn:QName((), 'src'))"
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
      new XQuery(compileChain, "let $doc := sdb:doc('mydocs.col', 'resource1') "
          + "let $stats := sdb:create-path-index($doc, '//*') " + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("Path index creation done.");
}
```

And in order to query the path index again some time later:

```java
// Query path index which are children of the log-element (only elements).
try (final var store = BasicXmlDBStore.newBuilder().build();
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Find path index for all elements which are children of the log-element (only elements).");
  
  final var node = (DBNode) new XQuery(new SirixCompileChain(store), "doc('mydocs.col')").execute(ctx);

  // We can simply use sdb:find-path-index('xs:node', 'xs:string') to find the appropriate index number and then scan the index.
  final var query = "let $doc := sdb:doc('mydocs.col', 'resource1') " + "return sdb:sort(sdb:scan-path-index($doc, "
      + "sdb:find-path-index($doc, '//log/*'), '//log/*'))";
  final var sortedSeq = new XQuery(compileChain, query).execute(ctx);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

Not that in this example we showed how to get access to the low-level transactional cursor API of Sirix and use this API.

In order to create a CAS index for all attributes, another one for text-nodes and a third one for all integers text-nodes:

```java
// Create and commit CAS indexes on all attribute- and text-nodes.
try (final var store = BasicXmlDBStore.newBuilder().build()
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println(
      "Create a CAS index for all attributes and another one for text-nodes. A third one is created for all integers:");
  final var query = new XQuery(compileChain,
      "let $doc := sdb:doc('mydocs.col', 'resource1') "
          + "let $casStats1 := sdb:create-cas-index($doc, 'xs:string', '//@*') "
          + "let $casStats2 := sdb:create-cas-index($doc, 'xs:string', '//*') "
          + "let $casStats3 := sdb:create-cas-index($doc, 'xs:integer', '//*') "
          + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println("");
  System.out.println("CAS index creation done.");
}
```

And to find and query the CAS-index (for all attribute values) again:

```java
// Query CAS index.
try (final var store = BasicXmlDBStore.newBuilder().build();
  final var ctx = SirixQueryContext.createWithNodeStore(store);
  final var compileChain = SirixCompileChain.createWithNodeStore(store)) {
  System.out.println("");
  System.out.println("Find CAS index for all attribute values.");
  
  final var sortedSeq =
      "let $doc := sdb:doc('mydocs.col', 'resource1') return sdb:sort(sdb:scan-cas-index($doc, sdb:find-cas-index($doc, 'xs:string', '//@*'), 'bar', true(), true(), 0, ()))";
  final var sortedSeq = new XQuery(compileChain, query).execute(ctx);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (final var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

In general for each index-type we have a function to create the index, to find the index-number for a given query again (the index definition must match) and to query the index.
