---
layout: documentation
doctitle: DOM-alike API
title: SirixDB - DOM-alike API
---

### Maven artifacts

First, you have to get the dependency on our Sirix query project. At this stage of development, please use the latest SNAPSHOT artifacts from the OSS snapshot repository. Just add the following repository section to your POM file:

```xml
<repository>
  <id>sonatype-nexus-snapshots</id>
  <name>Sonatype Nexus Snapshots</name> <url>https://oss.sonatype.org/content/repositories/snapshots</url>
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

Maven artifacts are deployed to the central maven repository (however, please use the SNAPSHOT-variants as of now). Currently, the following artifacts are available. Make sure that snapshots are getting updated with newer versions in your IDE.

Query project:

```xml
<dependency>
  <groupId>io.sirix</groupId>
  <artifactId>sirix-query</artifactId>
  <version>0.9.7-SNAPSHOT</version>
</dependency>
```

To add the dependency in Gradle:
```gradle
dependencies {
  compile 'io.sirix:sirix-query:0.9.7-SNAPSHOT'
}
```

### TODO

```xquery
let $doc := jn:open('mycol.jn','mydoc.jn', xs:dateTime('2019-04-13T16:24:27Z'))
let $statuses := $doc=>statuses
let $foundStatus := for $status in bit:array-values($statuses)
  let $dateTimeCreated := xs:dateTime($status=>created_at)
  where $dateTimeCreated > xs:dateTime("2018-02-01T00:00:00")
        and not(exists(jn:previous($status)))
  order by $dateTimeCreated
  return $status
return {"revision": sdb:revision($foundStatus), $foundStatus{text}}
```
