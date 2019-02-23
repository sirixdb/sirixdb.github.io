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

Maven artifacts are deployed to the central maven repository (however please use the SNAPSHOT-variants as of now). Currently the following artifacts are available. Make sure that snapshots are getting updated with newer versions in your IDE.

Core project:

```xml
<dependency>
  <groupId>io.sirix</groupId>
  <artifactId>sirix-xquery</artifactId>
  <version>0.9.0-SNAPSHOT</version>
</dependency>
```

To add the dependency in Gradle:
```gradle
dependencies {
  compile 'io.sirix:sirix-xquery:0.9.0-SNAPSHOT'
}
```

### Import and query
First, you might want to import an XML-document into Sirix and create a first database with the shredded/imported XML-document as a single resource file with the XQuery function `sdb:load(xs:string, xs:string, xs:string)`. The first argument is the database to create, the second the resource which represents the imported XML-document and the third parameter is the resource to import. Then loading the resource again and execute your first query (`sdb:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']`):

```java
final var doc = Paths.get("src", "main", "resources", "orga.xml");

// Initialize query context and store.
try (final var store = BasicDBStore.newBuilder().build()) {
  final var ctx1 = new SirixQueryContext(store);

  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var query1 = String.format("sdb:load('mydoc.col', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(xq1);
  new XQuery(query1).evaluate(ctx1);

  // Reuse store and query loaded document.
  final var ctx2 = new SirixQueryContext(store);
  System.out.println();
  System.out.println("Query loaded document:");
  final var xq2 = "sdb:doc('mydoc.col', 'mydoc.xml')/Organization/Project[@id='4711']";
  System.out.println(xq2);
  final var query = new XQuery(new SirixCompileChain(store), xq2);
  query.prettyPrint().serialize(ctx2, System.out);

  System.out.println();
}
```

Storing a collection of XML files in Sirix is as simple as using the following query for instance (dir is a directory path and you're importing all files with an `.xml` suffix):

```java
final var ctx = new SirixQueryContext(store);
final var query = String.format("bit:load('mydocs.col', io:ls('%s', '\\.xml$'))", dir);
new XQuery(query).evaluate(ctx);
```

And querying the collection is as simple as using the function collection:

```java
final var ctx = new SirixQueryContext(store);
final var query = "for $doc in collection('mydocs.col') return $doc";
new XQuery(query).setPrettyPrint(true).serialize(ctx, System.out);
```

### Update the resource

In order to update a resource you're able to use XQuery Update statements. First we load an XML-document again into a `database/resource` whereas the database is named `mycol.xml` and the resource `mydoc.xml`. Then we open the database/resource again in their most recent revision and insert an XML fragment (`<a><b/></a>`) as a first child into the root element log. The result is serialized to `STDOUT` again.

```java
// Prepare sample document.
final var doc = generateSampleDoc("sample");

// Initialize query context and store.
try (final var store = BasicDBStore.newBuilder().build()) {
  final var ctx1 = new SirixQueryContext(store);

  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var xq1 = String.format("sdb:load('mycol.xml', 'mydoc.xml', '%s')", docUri.toString());
  System.out.println(xq1);
  new XQuery(xq1).evaluate(ctx1);

  // Reuse store and query loaded document.
  final var ctx2 = new SirixQueryContext(store);
  System.out.println();
  System.out.println("Query loaded document:");
  final var xq2 = "let $doc := sdb:doc('mycol.xml', 'mydoc.xml')\n" + "let $log = $doc/log return \n"
    + "( insert nodes <a><b/></a> into $log )\n";
  System.out.println(xq2);
  new XQuery(xq2).execute(ctx2);

  final var query = new XQuery("sdb:doc('mycol.xml', 'mydoc.xml')");
  query.prettyPrint().serialize(ctx2, System.out);
  System.out.println();
}
```
Note, that a transaction is auto-commited in this case and that the element nodes `a` and `b` are stored in a new revision. Thus, in this case we open the most recent revision, which is revision two (bootstrapped revision is 0 with only a document-root node and revision 1 was the initially imported XML-document) and serialize it to `System.out`.

### Temporal axis
We not only provide all standard XPath axis, but also temporal XPath axis, which can be used to analyse how a resource or a subtree therein has changed between several revisions.

Temporal axis are compatible with node tests:

`<temporalaxis>::<nodetest>` is defined as `<temporalaxis>::*/self::<nodetest>`

For instance to simply serialize all revisions, we can use the axis `all-time::`

```java
try (final var store = BasicDBStore.newBuilder().build()) {
  final var ctx = new SirixQueryContext(store);
  System.out.println();
  System.out.println("Query loaded document:");
  final var queryString = "sdb:doc('mycol.xml', 'mydoc.xml')/log/all-time::*";
  System.out.println(xq3);
  final var query = new XQuery(new SirixCompileChain(store), queryString);
  query.prettyPrint().serialize(ctx, System.out);
}
```

We support a whole bunch of temporal axis: `first::` to get a node in the first revision, `last::` to get a node in the last revision, `previous::` to get the node in the previous revision, `next::` to get the node in the next revision, `future::` and `future-or-self::` to get a node in all future revisions or the current and future revisions, `past::` and `past-or-self::` to get a node in past revisions or the current and past revisions. We have already seen the `all-time::`-axis which iterates over a node in all revisions.

### Index structures
Index structures in Sirix are always user defined, typed indexes. We provide three types of indexes, name indexes on alement- or attribute-nodes in XML/XDM resources or name indexes on JSON object record keys, path indexes and so called content-and-structure (CAS)-indexes which are a kind of value on specific paths.

First, we create an element index on elements with the local name `src`:

```java
// Create and commit name index on all elements with QName 'src'.
try (final var store = BasicDBStore.newBuilder().build()) {
  final var ctx = new SirixQueryContext(store, CommitStrategy.EXPLICIT);
  System.out.println();
  System.out.println("Create name index for all elements with name 'src':");
  final var query = new XQuery(new SirixCompileChain(store),
        "let $doc := sdb:doc('mydocs.col', 'resource1', (), fn:boolean(1)) "
            + "let $stats := sdb:create-name-index($doc, fn:QName((), 'src')) "
            + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println();
  System.out.println("Name index creation done.");
}
```

And in order to query the name index again some time later:

```java
// Query name index.
try (final var store = BasicDBStore.newBuilder().build()) {
  System.out.println("");
  System.out.println("Query name index (src-element).");
  final var ctx = new QueryContext(store);
  final var queryString = "let $doc := sdb:doc('mydocs.col', 'resource1')"
      + " let $sequence := sdb:scan-name-index($doc, sdb:find-name-index($doc, fn:QName((), 'src')), fn:QName((), 'src'))"
      + " return sdb:sort($sequence)";
  final var query = new XQuery(new SirixCompileChain(store), queryString);
  query.prettyPrint();
  query.serialize(ctx, System.out);
}
```

In order to create a path index on all paths in the resource we can use:

```java
// Create and commit path index on all elements.
try (final var store = BasicDBStore.newBuilder().build()) {
  final var ctx = new QueryContext(store);
  System.out.println();
  System.out.println("Create path index for all elements (all paths):");
  final var query =
      new XQuery(new SirixCompileChain(store), "let $doc := sdb:doc('mydocs.col', 'resource1', (), fn:boolean(1)) "
          + "let $stats := sdb:create-path-index($doc, '//*') " + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println();
  System.out.println("Path index creation done.");
}
```

And in order to query the path index again some time later:

```java
// Query path index which are children of the log-element (only elements).
try (final BasicDBStore store = BasicDBStore.newBuilder().build()) {
  System.out.println("");
  System.out.println("Find path index for all elements which are children of the log-element (only elements).");
  final var ctx = new SirixQueryContext(store);
  final var node = (DBNode) new XQuery(new SirixCompileChain(store), "doc('mydocs.col')").execute(ctx);
  // We could do anything with the DBnode, for instance also getting the [transaction node cursor](/transactional-cursor-api.html) 
  // with the method getTrx().
  System.out.println(index);
  // Or simply use sdb:find-path-index('xs:node', 'xs:string') to find the appropriate index number and then scan the index.
  final var query = "let $doc := sdb:doc('mydocs.col', 'resource1') " + "return sdb:sort(sdb:scan-path-index($doc, "
      + "sdb:find-path-index($doc, '//log/*'), '//log/*'))";
  final var sortedSeq = new XQuery(new SirixCompileChain(store), query).execute(ctx3);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (final var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

Not that in this example we showed how to get access to the low-level transactional cursor API of Sirix and use this API.

In order to create a CAS index for all attributes, another one for text-nodes and a third one for all integers text-nodes:

```java
// Create and commit CAS indexes on all attribute- and text-nodes.
try (final BasicDBStore store = BasicDBStore.newBuilder().build()) {
  final QueryContext ctx = new QueryContext(store);
  System.out.println();
  System.out.println(
      "Create a CAS index for all attributes and another one for text-nodes. A third one is created for all integers:");
  final var query = new XQuery(new SirixCompileChain(store),
      "let $doc := sdb:doc('mydocs.col', 'resource1', (), fn:boolean(1)) "
          + "let $casStats1 := sdb:create-cas-index($doc, 'xs:string', '//@*') "
          + "let $casStats2 := sdb:create-cas-index($doc, 'xs:string', '//*') "
          + "let $casStats3 := sdb:create-cas-index($doc, 'xs:integer', '//*') "
          + "return <rev>{sdb:commit($doc)}</rev>");
  query.serialize(ctx, System.out);
  System.out.println();
  System.out.println("CAS index creation done.");
}
```

And to find and query the CAS-index (for all attribute values) again:

```java
// Query CAS index.
try (final var store = BasicDBStore.newBuilder().build()) {
  System.out.println("");
  System.out.println("Find CAS index for all attribute values.");
  final var ctx = new SirixQueryContext(store);
  final var sortedSeq =
      "let $doc := sdb:doc('mydocs.col', 'resource1') return sdb:sort(sdb:scan-cas-index($doc, sdb:find-cas-index($doc, 'xs:string', '//@*'), 'bar', true(), 0, ()))";
  final var sortedSeq = new XQuery(new SirixCompileChain(store), query).execute(ctx);
  final var sortedIter = sortedSeq.iterate();

  System.out.println("Sorted index entries in document order: ");
  for (final var item = sortedIter.next(); item != null; item = sortedIter.next()) {
    System.out.println(item);
  }
}
```

In general for each index-type we have a function to create the index, to find the index-number for a given query again (the index definition must match) and to query the index.
