---
layout: documentation
doctitle: Transactional cursor based API
---

### Maven artifacts

First, you have to get the decency on our Sirix core project. At this stage of development please use the latest SNAPSHOT artifacts from the OSS snapshot repository. Just add the following repository section to your POM file:

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
  <artifactId>sirix-core</artifactId>
  <version>0.9.0-SNAPSHOT</version>
</dependency>
```

To add the dependency in Gradle:
```gradle
dependencies {
  compile 'io.sirix:sirix-core:0.9.0-SNAPSHOT'
}
```

### Create a database with a single resource file
First, we want to show how to create a database with a single resource (the resource is going to be imported from an XML-document and shredded into our internal format).

```java
// XML-file to import.
final var pathToXmlFile = Paths.get("xmlFile");

// Create database configuration.
final var databaseFile = Paths.get("database");
final var dbConfig = new DatabaseConfiguration(databaseFile);

// Create a new lightweight database structure.
Databases.createXdmDatabase(dbConfig);

// Open the database.
try (final var database = Databases.openXdmDatabase(databaseFile)) {
  // Create a first resource without text-value compression but with DeweyIDs which are hierarchical node labels.
  database.createResource(ResourceConfiguration.builder("resource").useTextCompression(false).useDeweyIDs(true).build());

  try (// Open a resource manager.
       final var manager = database.openResourceManager("resource");
       // Open only write transaction on the resource (transaction provides a cursor for navigation
       // through moveToX-methods).
       final var wtx = manager.beginNodeTrx();
       final var fis = new FileInputStream(pathToXmlFile.toFile())) {
       
       // Import an XML document.
       wtx.insertSubtreeAsFirstChild(XmlShredder.createFileReader(fis));

       // Commit and persist the changes.
       wtx.commit();
  }
}
```
### Open the database and the resource manager again

Now, that we have imported a first resource and persisted it in our binary-structure, we are able to open it again at any time (alternatively the single node `read/write-transaction` handle can be reused after issuing the commit).

```java
// Open the database.
try (final var database = Databases.openXdmDatabase(databaseFile);
     final var manager = database.openResourceManager("resource");
     // Now open a read-only transaction again.
     final var rtx = manager.beginNodeReadOnlyTrx()) {
    
  // Use the descendant axis to iterate over all structural descendant nodes (each node with the exception of namespace- and attribute-nodes) in pre-order (depth-first).
  new DescendantAxis(rtx, IncludeSelf.YES).forEach((unused) -> {
    // The transaction-cursor is moved to each structural node (all nodes, except for namespace- and attributes in preorder).
    switch (rtx.getKind()) {
      case ELEMENT:
        // In order to process namespace-nodes we could do the following and log the full qualified name of each node.
        for (int i = 0, nspCount = rtx.getNamespaceCount(); i < nspCount; i++) {
          rtx.moveToNamespace(i);
          LOGGER.info(rtx.getName());
          rtx.moveToParent();
        }

        // In order to process attribute-nodes we could do the following and log the full qualified name of each node. 
        for (int i = 0, attrCount = rtx.getAttributeCount(); i < attrCount; i++) {
          rtx.moveToAttribute(i);
          LOGGER.info("Attribute name:" + rtx.getName());
          LOGGER.info("Attribute value:" + rtx.getValue());
          rtx.moveToParent();
        }
        break;
      case TEXT:
        // Log the text-value.
        LOGGER.info(rtx.getValue());
        break;
      // Other node types omitted.
      default:
        // Do nothing.
    };
  });
}
```
### Axis to navigate in space and in time
However as this is such a common case to iterate over structual and non-structural nodes as for instance namespace- and attribute-nodes we also provide a simple wrapper axis:

```java
new NonStructuralWrapperAxis(new DescendantAxis(rtx))
```

For sure we also have a `NamespaceAxis` and an `AttributeAxis`.

As it's very common to do something based on the different node-types we implemented the visitor pattern. As such you can simply plugin a visitor in another `descendant-axis` called `VisitorDescendantAxis`, which is a special axis taking care of the return types from the visit-methods. A visitor must implement methods as follows for each node:

```java
/**
 * Do something when visiting a {@link ImmutableElement}.
 * 
 * @param node the {@link ImmutableElement}
 */
VisitResult visit(ImmutableElement node);
```

The only implementation of the `VisitResult` interface is the following enum:

```java
/**
 * The result type of an {@link XdmNodeVisitor} implementation.
 * 
 * @author Johannes Lichtenberger, University of Konstanz
 */
public enum VisitResultType implements VisitResult {
  /** Continue without visiting the siblings of this node. */
  SKIPSIBLINGS,

  /** Continue without visiting the descendants of this node. */
  SKIPSUBTREE,

  /** Continue traversal. */
  CONTINUE,

  /** Terminate traversal. */
  TERMINATE
}
```

The `VisitorDescendantAxis` takes care and skips a whole subtree if the return type is `VisitResultType.SKIPSUBTREE`, or skips the traversal of all further right-siblings of the current node (`VisitResultType.SKIPSIBLINGS`). You can also terminate the whole traversal with `VisitResultType.TERMINATE`.

The default implementation of each method in the `Visitor`-interface returns `VisitResultType.CONTINUE` for each node-type, such that you only have to implement the methods (for the nodes), which you're interested in. If you've implemented a class called `MyVisitor` you can use the `VisitorDescendantAxis` in the following way:

```java
// Executes a modification visitor for each descendant node.
final var axis = VisitorDescendantAxis.newBuilder(rtx).includeSelf().visitor(new MyVisitor().build());
     
while (axis.hasNext()) axis.next();
```

We provide all possible `XPath` axis. Note, that the `PrecedingAxis` and the `PrecedingSiblingAxis` do not deliver nodes in document order, but in the natural encountered order. Furthermore a `PostOrderAxis` is available, which traverses the tree in a postorder traversal. Similarly a `LevelOrderAxis` traverses the tree in a breath first manner.

We provide several filters, which can be plugged in through a `FilterAxis`. The following code for instance traverses all children of a node and filters them for nodes with the local name "a".

```java
new FilterAxis<XdmNodeReadOnlyTrx>(new ChildAxis(rtx), new NameFilter(rtx, new QNm("a")))
```

The `FilterAxis` optionally takes more than one filter. The filter either is a `NameFilter`, to filter for names as for instance in elements and attributes, a value filter to filter text nodes or a node kind filter (`AttributeFilter`, `NamespaceFilter`, `CommentFilter`, `DocumentRootNodeFilter`, `ElementFilter`, `TextFilter` or `PIFilter` to filter processing instruction nodes).

Alternatively you could simply stream over your axis (without using the `FilterAxis` at all) and then filter by predicate. `rtx` is a `NodeReadOnlyTrx` in the following example:

```java
final var axis = new PostOrderAxis(rtx);
final var axisStream = StreamSupport.stream(axis.spliterator(), false);

axisStream.filter(unusedNodeKey -> new NameFilter(rtx, new QNm("a"))).forEach((unused) -> /* Do something with the transactional cursor */);
```

In order to achieve much more query power you can chain several axis with the `NestedAxis`. The following example shows how a simple XPath query can be processed. However, we think it's much more convenient simply use the XPath query with our Brackit binding.

```java
// XPath expression /p:a/b/text()
// Part: /p:a
final var childA = new FilterAxis(new ChildAxis(rtx), new NameFilter(rtx, "p:a"));
// Part: /b
final var childB = new FilterAxis(new ChildAxis(rtx), new NameFilter(rtx, "b"));
// Part: /text()
final var text = new FilterAxis(new ChildAxis(rtx), new TextFilter(rtx));
// Part: /p:a/b/text()
final var axis = new NestedAxis(new NestedAxis(childA, childB), text);
```

#### ConcurrentAxis
We also provide a ConcurrentAxis to fetch nodes concurrently. In order to execute an XPath-query as for instance `//regions/africa//location` it would look like that:

```java
final Axis axis = new NestedAxis(
        new NestedAxis(
            new ConcurrentAxis(firstConcurrRtx,
                new FilterAxis(new DescendantAxis(firstRtx, IncludeSelf.YES),
                    new NameFilter(firstRtx, "regions"))),
            new ConcurrentAxis(secondConcurrRtx,
                new FilterAxis(new ChildAxis(secondRtx), new NameFilter(secondRtx, "africa")))),
        new ConcurrentAxis(thirdConcurrRtx, new FilterAxis(
            new DescendantAxis(thirdRtx, IncludeSelf.YES), new NameFilter(thirdRtx, "location"))));
```

#### PredicateAxis
In order to test for a predicate for instance select all nodes which have a child element with name "foo" you could use:

```java
final var childAxisFilter = new FilterAxis(new ChildAxis(rtx), new ElementFilter(rtx), new NameFilter("foo"));
final var descendantAxis = new DescendantAxis();
final var predicateAxisFilter = new PredicateAxis(rtx, childAxisFilter);
final var nestedAxis = new NestedAxis(descendantAxis, predicateAxisFilter);
```

#### Time Travel axis

However, we not only support navigational axis within one revision, we also allow navigation on the time axis.

For instance you can use one of the following axis to navigate in time:
`FirstAxis`, `LastAxis`, `PreviousAxis`, `NextAxis`, `AllTimeAxis`, `FutureAxis`, `PastAxis`.

Each of the constructors of these time-travel axis takes a transactional cursor as the only parameter and opens the node, the cursor currently points to in each of the revisions (if it exists).

     // Commit second version.
     wtx.commit();

      // Transaction handle is relocated at the document node of the new revision; iterate over "normal" descendant axis.
      final Axis axis = new DescendantAxis(wtx);
      if (axis.hasNext()) {
        axis.next();

        switch (wtx.getKind()) {
        case ELEMENT:
          // In order to process namespace-nodes we could do the following and log the full qualified name of each node.
          for (int i = 0, nspCount = rtx.getNamespaceCount(); i < nspCount; i++) {
            rtx.moveToNamespace(i);
            LOGGER.info(rtx.getName());
            rtx.moveToParent();
          }

          // In order to process attribute-nodes we could do the following and log the full qualified name of each node. 
          for (int i = 0, attrCount = rtx.getAttributeCount(); i < attrCount; i++) {
            rtx.moveToAttribute(i);
            LOGGER.info(rtx.getName());
            rtx.moveToParent();
          }
          break;
        default:
          // Do nothing.
      }
      if (wtx.moveTo(axis.peek()).get().isComment()) {
        LOGGER.info(wtx.getValue());
      }

      // Begin a reading transaction on revision 0 concurrently to the write-transaction on revision 1 (the very first commited revision).
      try (final var rtx = resource.beginNodeReadOnlyTrx(0);) {
        // moveToX-methods returns either Moved or NotMoved whereas you can query if it has been moved or not, for instance via
        rtx.moveToFirstChild();

        if (rtx.moveToFirstChild().hasMoved())
          // Do something.

        // A fluent call would be if you know a node has a right sibling and there's a first child of the right sibling.
        rtx.moveToRightSibling().get().moveToFirstChild().get();

        // Can be tested before.
        if (rtx.hasRightSibling()) {
          rtx.moveToRightSibling();
        }

        // Move to next node in the XPath following::-axis.
        rtx.moveToNextFollowing();

        // Move to previous node in preorder.
        rtx.moveToPrevious();

        // Move to next node in preorder.
        rtx.moveToNext();

        /* 
         * Or simply within the move-operation and a postcondition check. If hasMoved() returns false, the transaction isn't moved.
         */
        if (rtx.moveToRightSibling().hasMoved()) {
          // Do something.
        }

      // Instead of the following, a visitor is useable!
      switch (rtx.getKind()) {
      case ELEMENT:
        for (int i = 0, nspCount = rtx.getNamespaceCount(); i < nspCount; i++) {
          rtx.moveToNamespace(i);
          LOGGER.info(rtx.getName());
          rtx.moveToParent();
        }

        for (int i = 0, attrCount = rtx.getAttributeCount(); i < attrCount; i++) {
          rtx.moveToAttribute(i);
          LOGGER.info(rtx.getName());
          rtx.moveToParent();
        }

        // Move to the specified attribute by name.
        rtx.moveToAttributeByName(new QNm("foobar"));
        rtx.moveToParent();
        
        LOGGER.info(rtx.getDescendantCount());
        LOGGER.info(rtx.getChildCount());
        /* 
         * Hash of a node, build bottom up for all nodes (depends on descendant hashes, however only
         * ancestor nodes are updated during a normal edit-operation. During bulk inserts with 
         * insertSubtree(...) the hashes are generated during a postorder-traversal, just like the 
         * descendant-count of each structural node.
         */
        LOGGER.info(rtx.getHash());
        break;
      case TEXT:
        LOGGER.info(rtx.getValue());
        break;
      case COMMENT:
        LOGGER.info(rtx.getValue());
        break;
      default:
        throw new IllegalStateException("Node kind not known!");
    }
  }
```
For printing the whole XML document:
```java
final var serializer = XmlSerializer.newBuilder(manager, System.out).prettyPrint().build();
serializer.call();
```
Or write it to string:
```java
ByteArrayOutputStream baos = new ByteArrayOutputStream();
PrintStream writer = new PrintStream(baos);
final XmlSerializer serializer = XmlSerializer.newBuilder(manager, writer).prettyPrint().build();
serializer.call();
String content = baos.toString(StandardCharsets.UTF8);
```

Note that we aim to support all the Guava flavor. Just imagine how nice the following is:
```java
final Iterator<Long> results = FluentIterable.from(new DescendantAxis(rtx)).filter(new ElementFilter(rtx)).limit(2).iterator();
```

to filter all element nodes and skip after the first 2 elements are found. The resulting iterator contains at most 2 resulting unique node-keys (IDs) to which we can navigate through rtx.moveTo(long).

Furthermore a FilterAxis(Axis, Filter, Filter...) is usable. It's first parameter is the axis to use, the second parameter is a filter. Optionally further filters are usable (third varargs parameter).

To update a resource with algorithmically found differences between two tree-structures, use something like the following:

```java
// Old Sirix resource to update.
final var resOldRev = Paths.get(args[0]);

// XML document which should be imported as the new revision.
final var resNewRev = Paths.get(args[1]);

// Determine and import differences between the sirix resource and the
// provided XML document.
FMSEImport.xdmDataImport(resOldRev, resNewRev);
```

Method chaining for insertions:

```java
// Setup everything omitted... write transaction opened. Assertion: wtx is located at element node.
wtx.insertAttribute(new QNm("foo"), "bar", Move.PARENT).insertElementAsRightSibling(new QNm("baz"));

// Copy subtree of the node the read-transaction is located at as a new right sibling.
wtx.copySubtreeAsRightSibling(rtx);
```

Similarly moveToX()-methods are usable:

```java
// Get returns the transaction cursor currently used. However in this case the caller must be sure that a right sibling of the node denoted by node-key 15 and his right sibling and the right sibling's first child exists.
wtx.moveTo(15).getNodeCursor().moveToRightSibling().getNodeCursor().moveToFirstChild().getNodeCursor().insertCommentAsFirstChild("foo");
```

A whole bunch of axis are usable (all XPath axis and a few more):

```java
// Simple postorder-axis which iterates in postorder through a (sub)tree.
final var axis = new PostOrderAxis<XdmNodeReadOnlyTrx>(rtx); 
while (axis.hasNext()) {
  // Unique node identifier (nodeKey) however not needed here.
  final long nodeKey = axis.next();
  // axis.getTrx() or directly use rtx.
  switch(axis.getTrx().getKind()) {
  case TEXT:
    // Do something.
    break;
  }
}
```

or more elegantly:

```java
// Iterate and use a visitor implementation to describe the behavior for the individual node types.
final var visitor = new MyVisitor(rtx);
final var axis = new PostOrderAxis<XdmNodeReadOnlyTrx>(rtx); 
while (axis.hasNext()) {
  axis.next();
  rtx.acceptVisitor(visitor);
}
```

or with the foreach-loop:
```java
// Iterate and use a visitor implementation to describe the behavior for the individual node types.
final var visitor = new MyVisitor(rtx);
for (final long nodeKey : new PostOrderAxis(rtx)) {
  rtx.acceptVisitor(visitor);
}
```

Furthermore a special filter-axis is provided:

``` 
// Filter by name (first argument is the axis, next arguments are filters (which implement org.sirix.axis.filter.Filter).
for (final var axis = new FilterAxis<XdmNodeReadOnlyTrx>(new VisitorDescendantAxis.Builder(rtx).includeSelf().visitor(Optional.of(visitor)).build(), new NameFilter(rtx, "foobar")); axis.hasNext();) {
  axis.next();
}
```

Further filters can be specified. All XPath axis are also available, plus a LevelOrderAxis, a ConcurrentAxis which executes the specified axis concurrently. Furthermore a ConcurrentUnionAxis, ConcurrentExceptAxis, ConcurrentIntersectAxis are provided. To allow chained axis, a `NestedAxis` is available which takes two axis as arguments.

The VisitorDescendantAxis above is especially useful as it executes a visitor as one of the first things in the hasNext() iterator-method. The return value of the visitor is used to guide the preorder traversal:

```java
/**
 * The result type of a {@link Visitor} implementation.
 * 
 * @author Johannes Lichtenberger, University of Konstanz
 */
public enum VisitResult {
  /** Continue without visiting the siblings of this structural node. */
  SKIPSIBLINGS,

  /** Continue without visiting the descendants of this element. */
  SKIPSUBTREE,

  /** Continue traversal. */
  CONTINUE,

  /** Terminate traversal. */
  TERMINATE,
}
```

Temporal axis to navigate not only in space, but also in time are also available (for instance to iterate over all future revisions, all past revisions, the last revision, the first revision, a specific revision, the previous revision, the next revision...)

