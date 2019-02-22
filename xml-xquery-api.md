---
layout: documentation
doctitle: XML/XDM XQuery-API
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

### Load/Import your first XML-document into a Sirix database / resource and execute your first query
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
