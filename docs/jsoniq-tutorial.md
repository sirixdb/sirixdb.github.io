---
layout: documentation
doctitle: Using the Java CLI via JSONiq queries
title: SirixDB - Using the Java CLI via JSONiq queries
---

# Tutorial for using the Java CLI and JSONiq queries

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

In order to query the contents we can simply open the database:

```xquery
jn:collection('mycol')
```
The quey result will be: `{"foo":true} ["bla","blubb"]`

Th
