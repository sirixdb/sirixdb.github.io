---
layout: documentation
doctitle: Using the Java CLI via JSONiq queries
title: SirixDB - Using the Java CLI via JSONiq queries
---

## Setup a Shell
First, you should make sure to download the current sirix-query-all.jar (SNAPSHOT)-release from [the OSS snapshot repository](https://oss.sonatype.org/content/repositories/snapshots/io/sirix/) in the `sirix-query` subfolder-

You can then add a shell script on linux(like) systems, for instance named `sirix-shell.sh`:

```bash
#!/bin/bash

java -DLOGGER_HOME=~/sirix-data -Xms3g -Xmx8g --enable-preview --add-exports=java.base/jdk.internal.ref=ALL-UNNAMED --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED -XX:+UseZGC -jar sirix-query-0.10.4-all.jar -iq
```

Make sure to adapt the JAR file to the downloaded version.

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

In order to query the contents we can open the database using the `jn:collection` function:

```xquery
jn:collection('mycol')
```

The quey result will be: `{"foo":true} ["bla","blubb"]`

Of course you can query single documents either by looping over the result of `jn:collection` or via `jn:doc`:

```xquery
jn:doc('mycol.jn','resource1')
```

```xquery
jn:doc('mycol.jn','resource2')
```


## Updates

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

```
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
return {"revision": $revision, "timestamp":sdb:timestamp($revision), "data": $revision}
```

Result is:

```json
{"revision":{"foo":true},"timestamp":"2023-11-19T22:17:55:717000Z","data":{"foo":true}} {"revision":{"bar":true},"timestamp":"2023-11-19T22:19:38:157000Z","data":{"bar":true}} {"revision":{"bar":false},"timestamp":"2023-11-20T17:59:38:68000Z","data":{"bar":false}}
```

The timestamps are the transactional commit timestamps, the system time when data is known to the system (one axis of the bitemporality).
