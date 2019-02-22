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

### First steps
First, you might want to import an XML-document into Sirix and make sure it's serialized form represents the same XML-document:

```java
final var doc = Paths.get("src", "main", "resources", "test.xml");

// Initialize query context and store.
try (final var store = BasicDBStore.newBuilder().build()) {
  final var compileChain = new SirixCompileChain(store);
  final var ctx1 = new SirixQueryContext(store);

  // Use XQuery to load sample document into store.
  System.out.println("Loading document:");
  final var docUri = doc.toUri();
  final var xq1 = String.format("bit:load('mydoc.xml', '%s')", docUri.toString());
  System.out.println(xq1);
  new XQuery(xq1).evaluate(ctx1);

  // Reuse store and query loaded document.
  final var ctx2 = new SirixQueryContext(store);
  System.out.println();
  System.out.println("Query loaded document:");
  final String xq2 = "doc('mydoc.xml')//*";
  
  System.out.println(xq2);
  final var query = new XQuery(compileChain, xq2);
  query.prettyPrint().serialize(ctx2, System.out);

  System.out.println();
}
```
