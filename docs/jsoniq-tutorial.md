---
layout: documentation
doctitle: Using the Java CLI via JSONiq queries
title: SirixDB - Using the Java CLI via JSONiq queries
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/jsoniq-tutorial.md)

## Setup a Shell
First, you should make sure to download the current sirix-query-all.jar (SNAPSHOT)-release from [the OSS snapshot repository](https://oss.sonatype.org/content/repositories/snapshots/io/sirix/) in the `sirix-query` subfolder. (or you can get it locally in your `/bundles/sirix-query/build/libs` directory after doing `./gradlew build`)

You can then add a shell script on linux(like) systems, for instance named `sirix-shell.sh`:

```bash
#!/bin/bash

java -DLOGGER_HOME=~/sirix-data -Xms3g -Xmx8g --enable-preview --add-exports=java.base/jdk.internal.ref=ALL-UNNAMED --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED -XX:+UseZGC -jar sirix-query-0.10.4-all.jar -iq
```

Make sure to adapt the JAR file to the downloaded version. (Rename the JAR `sirix-query-0.10.4-all.jar` in `sirix-shell.sh` script to the JAR you are using)

In order to execute queries, open sirix shell through following command:

```xquery
./sirix-shell.sh
```

Example to execute queries: 

```xquery
sirix > let $doc := jn:doc('mycol.jn','resource2')
> return rename json $doc.foo as "bar"
> (make sure to give last as NULL, Simply Enter)

Query result:
//RESULT
```

On Windows, you can create a batch file accordingly.

## Import of data
[Download and unpack](https://github.com/sirixdb/sirixdb.github.io/raw/master/files/json.tar.gz) a zipped directory with two simple JSON files, an `object.json` and an `array.json` file into the same directory as the JAR and the shell-script.

The array JSON file is as simple as:

```json
["bla", "blubb"]
```

The object JSON file:

```json
{"foo": true}
```

Now we can import the directory into a SirixDB `database` as follows:

```xquery
jn:load('mycol', (), io:ls('/path/to/your/json/directory', '\\.json$'))
```

If your JSON directory (named `json`) is in same folder as `sirix-shell.sh` and JAR, give path to query as follows:

```xquery
jn:load('mycol', (), io:ls('json', '\\.json$'))
```

In order to query the contents we can open the database using the `jn:collection` function:

```xquery
jn:collection('mycol')
```

The quey result will be:

```json
{"foo":true} ["bla","blubb"]
```

Of course you can query single documents either by looping over the result of `jn:collection` or via `jn:doc`:

```xquery
jn:doc('mycol.jn','resource1')
```

```xquery
jn:doc('mycol.jn','resource2')
```


## Updates and time travel queries

You can update `resource2` in the database/collection `mycol.jn` via JSONiq update statements:

```xquery
let $doc := jn:doc('mycol.jn','resource2')
return rename json $doc.foo as "bar"
```
This query renames the field `foo` to `bar`. The implicit read-write transaction is automatically committed.

SirixDB only ever appends data and never overwrites old revisions. Thus, we can, of course, load the first revision via an optional third parameter to the `jn:doc` function:

```xquery
jn:doc('mycol.jn','resource2',1)
```

will retrieve the first revision of the resource:

```json
{"foo":true}
```

The new revision can be queried using (we can omit specifying revision 2 as it's equivalent):

```xquery
jn:doc('mycol.jn','resource2',2)
```

Result is:

```json
{"bar":true}
```

### Time travel functions to retrieve the state of nodes in different revisions

With the function `jn:all-times` we can retrieve all revisions of the resource (or any node in the revision):

```xquery
jn:all-times(jn:doc('mycol.jn','resource2'))
```

Result is:

```json
{"foo":true} {"bar":true}
```

Other temporal functions exist to navigate not only in space, but also in time.
- `jn:previous`: Retrieve the node in the previous revision
- `jn:next`: Retrieve the node in the next revision
- `jn:first`: Retrieve the node in the first revision
- `jn:last`: Retrieve the node in the last revision
- `jn:future`: Retrieve the node in the future revisions
- `jn:past`: Retrieve the node in the past revisions

we can also change the value via:

```xquery
let $doc := jn:doc('mycol.jn','resource2')
return replace json value of $doc.bar with false
```

Thus, we now have 3 revisions:

```xquery
let $revisions := jn:all-times(jn:doc('mycol.jn','resource2'))
for $revision in $revisions
return {"revision": sdb:revision($revision), "timestamp":sdb:timestamp($revision), "data": $revision}
```

Result is:

```json
{"revision":1,"timestamp":"2023-11-19T22:17:55:717000Z","data":{"foo":true}} {"revision":2,"timestamp":"2023-11-19T22:19:38:157000Z","data":{"bar":true}} {"revision":3,"timestamp":"2023-11-20T17:59:38:68000Z","data":{"bar":false}}
```

The timestamps are the transactional commit timestamps, the system time when data is known to the system (one axis of the bitemporality).

If we want to search for a specific timestamp, we can for instance specify:

```xquery
jn:open('mycol.jn','resource2',xs:dateTime('2023-11-19T22:23:00'))
```

The result is the second revision (as the third revision was committed one day later):

```json
{"bar":true}
```
### System Time: retrieve all states of a resource between two given timestamps 
If you want to retrieve all states of a resource between two timestamps (transaction/system commit time), you can invoke the following:

```xquery
let $revisions := jn:open-revisions('mycol.jn','resource2',xs:dateTime('2023-11-19T00:00:00-00:00'),xs:dateTime('2023-11-19T23:00:00-00:00'))
for $revision in $revisions
return {"revision": sdb:revision($revision), "timestamp":sdb:timestamp($revision), "data": $revision}
```

The result for my database is as follows:

```json
{"revision":1,"timestamp":"2023-11-19T22:17:55:717000Z","data":{"foo":true}} {"revision":2,"timestamp":"2023-11-19T22:19:38:157000Z","data":{"bar":true}}
```

Of course, the system times when a specific revision has been created are different on your computer.

### Change tracking: what has been changed between consecutive revisions
To check what has been updated between revisions of a resource we can use the following query:

```xquery
let $maxRevision := sdb:revision(jn:doc('mycol.jn','resource2'))
let $result := for $i in (1 to $maxRevision)
               return
                 if ($i > 1) then
                   jn:diff('mycol.jn','resource2',$i - 1, $i)
                 else
                   ()
return [
  for $diff at $pos in $result
  return {"diffRev" || $pos || "toRev" || $pos + 1: jn:parse($diff).diffs}
]
```

Result is:

```json
[{"diffRev1toRev2":[{"update":{"nodeKey":2,"deweyID":"1.17.17","depth":2,"name":"bar"}}]},{"diffRev2toRev3":[{"replace":{"oldNodeKey":3,"newNodeKey":4,"deweyID":"1.17.17.0","depth":2,"type":"boolean","data":false}}]}]
```
Each node is assigned a unique, monotonically increasing 64Bit `nodeKey` (`ID`), which never changes and is not reassigned once the node has been removed.
In our example we first updated the field name in revision 2 to `"bar"`. We then replace the value, the node with `nodeKey` 3 and `true` with a new node getting `nodeKey` 4 assigned having the value `false`.

## Adding a database/resource from a specific URL
We can also add resources from a specific URL (as in this [Twitter](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/test/resources/json/twitter.json) example):

```xquery
jn:load('mycol.jn','mydoc.jn','https://raw.githubusercontent.com/sirixdb/sirix/main/bundles/sirix-core/src/test/resources/json/twitter.json')
```

## Indexing


### Name / object field indexes

```xquery
jn:store('json-path1','mydoc.jn','[{"test": "test string"},{"test": ["a", {"testfield": "test blabla string", "foo": {"testfield": true}}, null, "b", "c"]}]')
```

```xquery
let $doc := jn:doc('mycol.jn','mydoc.jn')
let $stats := jn:create-name-index($doc, ('testfield','test'))
return {"revision": sdb:commit($doc)}
```

```xquery
let $doc := jn:doc('mycol.jn','mydoc.jn')
let $nameIndexNumber := jn:find-name-index($doc, 'testfield')
for $node in jn:scan-name-index($doc, $nameIndexNumber, 'testfield')
order by sdb:revision($node), sdb:nodekey($node)
return {"nodeKey": sdb:nodekey($node), "path": sdb:path($node), "revision": sdb:revision($node)}
```

### Path indexes

### CAS (content-and-structure) indexes

```xquery
jn:store('json-path1','mydoc.jn','[{"test": "test string"},{"test": ["a", {"blabla": "test blabla string"}, null, "b", "c"]}]')
```

```xquery
let $doc := jn:doc('json-path1','mydoc.jn')
let $stats := jn:create-cas-index($doc, 'xs:string', '//[]')
return {"revision": sdb:commit($doc)}
```

```xquery
let $doc := jn:doc('json-path1','mydoc.jn')
let $casIndexNumber := jn:find-cas-index($doc, 'xs:string', '/[]/test/[]')
for $node in jn:scan-cas-index($doc, $casIndexNumber, 'b', '==', '/[]/test/[]')
order by sdb:revision($node), sdb:nodekey($node)
return {"nodeKey": sdb:nodekey($node), "node": $node, "path": sdb:path(sdb:select-parent($node))}
```
