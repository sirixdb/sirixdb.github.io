---
layout: documentation
doctitle: Using the Java CLI via JSONiq queries
title: SirixDB - Using the Java CLI via JSONiq queries
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/jsoniq-tutorial.md)

## Setup a Shell
Follow the [source-build prerequisites](/docs/operations.html#1-supported-environment)
and build the query module's distribution from a SirixDB checkout:

```bash
./gradlew :sirix-query:installDist
bundles/sirix-query/build/install/sirix-query/bin/sirix-query -iq
```

The generated launcher includes the module's JVM arguments. On Windows use the
corresponding `sirix-query.bat` launcher. The `-iq` option starts interactive query
input; enter a blank line after each query to evaluate it.

## Import of data
[Download and unpack](/files/json.tar.gz) the archive containing `object.json` and
`array.json`. Use their extracted paths in the import queries below.

The array JSON file is as simple as:

```json
["bla", "blubb"]
```

The object JSON file:

```json
{"foo": true}
```

Import the files with explicit resource names so the queries below use the same
names on every run. Replace the paths with the extracted files' locations:

```xquery
jn:load('mycol', 'resource1', '/path/to/json/array.json')
```

```xquery
jn:load('mycol', 'resource2', '/path/to/json/object.json', false())
```

In order to query the contents we can open the database using the `jn:collection` function:

```xquery
jn:collection('mycol')
```

The query result will be:

```json
{"foo":true} ["bla","blubb"]
```

Of course you can query single documents either by looping over the result of `jn:collection` or via `jn:doc`:

```xquery
jn:doc('mycol','resource1')
```

```xquery
jn:doc('mycol','resource2')
```


## Updates and time travel queries

See [JSONiq Update Patterns](/docs/jsoniq-update-patterns.html) for a walkthrough of nested updates and the revisions they create.

You can update `resource2` in the database/collection `mycol` via JSONiq update statements:

```xquery
let $doc := jn:doc('mycol','resource2')
return rename json $doc.foo as "bar"
```
This query renames the field `foo` to `bar`. The implicit read-write transaction is automatically committed.

SirixDB only ever appends data and never overwrites old revisions. Thus, we can, of course, load the first revision via an optional third parameter to the `jn:doc` function:

```xquery
jn:doc('mycol','resource2',1)
```

will retrieve the first revision of the resource:

```json
{"foo":true}
```

The new revision can be queried using (we can omit specifying revision 2 as it's equivalent):

```xquery
jn:doc('mycol','resource2',2)
```

Result is:

```json
{"bar":true}
```

### Time travel functions to retrieve the state of nodes in different revisions

With the function `jn:all-times` we can retrieve all revisions of the resource (or any node in the revision):

```xquery
jn:all-times(jn:doc('mycol','resource2'))
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
let $doc := jn:doc('mycol','resource2')
return replace json value of $doc.bar with false
```

Thus, we now have 3 revisions:

```xquery
let $revisions := jn:all-times(jn:doc('mycol','resource2'))
for $revision in $revisions
return {"revision": sdb:revision($revision), "timestamp":sdb:timestamp($revision), "data": $revision}
```

Result is:

```json
{"revision":1,"timestamp":"2023-11-19T22:17:55.717000Z","data":{"foo":true}} {"revision":2,"timestamp":"2023-11-19T22:19:38.157000Z","data":{"bar":true}} {"revision":3,"timestamp":"2023-11-20T17:59:38.068000Z","data":{"bar":false}}
```

The timestamps are the transactional commit timestamps, the system time when data is known to the system (one axis of the bitemporality).

If we want to search for a specific timestamp, we can for instance specify:

```xquery
jn:open('mycol','resource2',xs:dateTime('2023-11-19T22:23:00'))
```

The result is the second revision (as the third revision was committed one day later):

```json
{"bar":true}
```
### System Time: retrieve all states of a resource between two given timestamps
If you want to retrieve all states of a resource between two timestamps (transaction/system commit time), you can invoke the following:

```xquery
let $revisions := jn:open-revisions('mycol','resource2',xs:dateTime('2023-11-19T00:00:00-00:00'),xs:dateTime('2023-11-19T23:00:00-00:00'))
for $revision in $revisions
return {"revision": sdb:revision($revision), "timestamp":sdb:timestamp($revision), "data": $revision}
```

The result for my database is as follows:

```json
{"revision":1,"timestamp":"2023-11-19T22:17:55.717000Z","data":{"foo":true}} {"revision":2,"timestamp":"2023-11-19T22:19:38.157000Z","data":{"bar":true}}
```

Of course, the system times when a specific revision has been created are different on your computer.

### Change tracking: what has been changed between consecutive revisions
To check what has been updated between revisions of a resource we can use the following query:

```xquery
let $maxRevision := sdb:revision(jn:doc('mycol','resource2'))
let $result := for $i in (1 to $maxRevision)
               return
                 if ($i > 1) then
                   jn:diff('mycol','resource2',$i - 1, $i)
                 else
                   ()
return [
  for $diff at $pos in $result
  return {"diffRev" || $pos || "toRev" || $pos + 1: $diff.diffs}
]
```

The update payloads include these fields (path and DeweyID metadata omitted):

```json
[{"diffRev1toRev2":[{"update":{"nodeKey":2,"name":"bar"}}]},{"diffRev2toRev3":[{"update":{"nodeKey":2,"type":"boolean","value":false}}]}]
```
Each node is assigned a unique, monotonically increasing 64Bit `nodeKey` (`ID`), which never changes and is not reassigned once the node has been removed.
The field name and boolean value share one `OBJECT_NAMED_BOOLEAN` node with `nodeKey` 2. Revision 2 renames that node to `"bar"`; revision 3 updates its value from `true` to `false`. Both updates preserve the node key, so its history remains continuous.

## Adding a database/resource from a specific URL
Pass `false()` as the fourth argument to preserve the existing database and its revision history when adding a resource from a URL (as in this [Twitter](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-core/src/test/resources/json/twitter.json) example):

```xquery
jn:load('mycol','mydoc.jn','https://raw.githubusercontent.com/sirixdb/sirix/main/bundles/sirix-core/src/test/resources/json/twitter.json', false())
```

## Indexing


### Name / object field indexes

```xquery
jn:store('json-path1','mydoc.jn','[{"test": "test string"},{"test": ["a", {"testfield": "test blabla string", "foo": {"testfield": true}}, null, "b", "c"]}]')
```

```xquery
let $doc := jn:doc('json-path1','mydoc.jn')
let $stats := jn:create-name-index($doc, ('testfield','test'))
return {"revision": sdb:commit($doc)}
```

```xquery
let $doc := jn:doc('json-path1','mydoc.jn')
let $nameIndexNumber := jn:find-name-index($doc, 'testfield')
for $node in jn:scan-name-index($doc, $nameIndexNumber, 'testfield')
order by sdb:revision($node), sdb:nodekey($node)
return {"nodeKey": sdb:nodekey($node), "path": sdb:path($node), "revision": sdb:revision($node)}
```

For path index creation and scans, see the [function reference](/docs/jsoniq-functions.html#indexes).

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
