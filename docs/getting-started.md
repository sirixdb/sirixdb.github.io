---
layout: documentation
doctitle: Getting Started
title: SirixDB - Getting Started
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/getting-started.md)

Get SirixDB running and query temporal data in minutes. Pick the path that fits your use case:

| Path | Time | Best for |
|---|---|---|
| [Web GUI Demo](#web-gui-demo) | ~2 min | Exploring the UI, visualizing revisions and diffs |
| [REST API](#rest-api) | ~5 min | Building web/mobile apps, language-agnostic integration |
| [Embedded Java Library](#embedded-java-library) | ~10 min | JVM applications, maximum performance, full control |
| [CLI Tools](#cli-tools) | ~10 min | Ad-hoc queries, scripting, interactive JSONiq |

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) for the first two paths, [JDK 24+](https://jdk.java.net/) for the last two.

---

## Web GUI Demo

The fastest way to see SirixDB in action. The demo starts a pre-loaded SirixDB instance with sample data and a web frontend.

**1. Clone and start:**

```bash
git clone https://github.com/sirixdb/sirixdb-web-gui.git
cd sirixdb-web-gui
docker compose -f docker-compose.demo.yml up --build
```

**2. Open the GUI:**

Navigate to [http://localhost:3000](http://localhost:3000) and log in with `admin` / `admin`.

**3. Explore:**

- **Tree view** — browse the JSON document structure
- **Revision timeline** — step through the full history of a resource
- **Diff viewer** — compare any two revisions side by side
- **Query editor** — run JSONiq queries against any revision

**4. Tear down:**

```bash
docker compose -f docker-compose.demo.yml down -v
```

---

## REST API

Start a full SirixDB server with Keycloak authentication and interact via curl.

### Start the server

```bash
git clone https://github.com/sirixdb/sirix.git
cd sirix
docker compose up -d
```

Wait for Keycloak's health check to pass (~30 s), then the SirixDB server starts on `https://localhost:9443`.

### Authenticate

```bash
TOKEN=$(curl -sk -X POST "https://localhost:9443/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Store a JSON document

```bash
curl -sk -X PUT "https://localhost:9443/shop/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '[
    {"name": "Laptop", "price": 999},
    {"name": "Phone",  "price": 699},
    {"name": "Tablet", "price": 449}
  ]'
```

This creates a JSON database called `shop` with a resource called `products` — revision 1.

### Read it back

```bash
curl -sk "https://localhost:9443/shop/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

### Update the document (revision 2)

First, get the ETag of the root node:

```bash
ETAG=$(curl -skI "https://localhost:9443/shop/products?nodeId=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  | grep -i etag | tr -d '\r' | cut -d' ' -f2)
```

Then insert a new product:

```bash
curl -sk -X POST "https://localhost:9443/shop/products?nodeId=1&insert=asFirstChild" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "ETag: $ETAG" \
  -d '{"name": "Monitor", "price": 349}'
```

### Time travel — read revision 1

```bash
curl -sk "https://localhost:9443/shop/products?revision=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

### Diff two revisions

```bash
curl -sk "https://localhost:9443/shop/products/diff?first-revision=1&second-revision=2" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

### Temporal JSONiq query

Retrieve all revisions of the entire document:

```bash
curl -sk -X POST "https://localhost:9443/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"query": "jn:all-times(jn:doc(\"shop\",\"products\"))"}'
```

### Tear down

```bash
docker compose down -v
```

For the full endpoint reference, see [REST API](/docs/rest-api.html).

---

## Embedded Java Library

Use SirixDB directly inside your JVM application for maximum performance and fine-grained control.

### Add the dependency

**Gradle (Kotlin DSL):**

```kotlin
repositories {
    mavenCentral()
    maven("https://oss.sonatype.org/content/repositories/snapshots/")
}

dependencies {
    implementation("io.sirix:sirix-core:0.11.1-SNAPSHOT")
}
```

**Maven:**

```xml
<repositories>
  <repository>
    <id>sonatype-snapshots</id>
    <url>https://oss.sonatype.org/content/repositories/snapshots/</url>
    <snapshots><enabled>true</enabled></snapshots>
  </repository>
</repositories>

<dependencies>
  <dependency>
    <groupId>io.sirix</groupId>
    <artifactId>sirix-core</artifactId>
    <version>0.11.1-SNAPSHOT</version>
  </dependency>
</dependencies>
```

### Complete example

```java
import io.sirix.access.DatabaseConfiguration;
import io.sirix.access.Databases;
import io.sirix.access.ResourceConfiguration;
import io.sirix.api.JsonNodeReadOnlyTrx;
import io.sirix.api.JsonNodeTrx;
import io.sirix.api.json.JsonResourceSession;
import io.sirix.service.json.serialize.JsonSerializer;
import io.sirix.service.json.shredder.JsonShredder;

import java.io.StringWriter;
import java.nio.file.Files;
import java.nio.file.Path;

public class SirixQuickStart {
    public static void main(String[] args) throws Exception {
        final var dbPath = Path.of(System.getProperty("java.io.tmpdir"), "sirix-getting-started");

        // Clean up from previous runs
        if (Files.exists(dbPath)) {
            Databases.removeDatabase(dbPath);
        }

        // 1. Create a database and resource
        Databases.createJsonDatabase(new DatabaseConfiguration(dbPath));

        try (final var database = Databases.openJsonDatabase(dbPath)) {
            database.createResource(ResourceConfiguration.newBuilder("products").build());

            // 2. Insert JSON data (revision 1)
            try (final var session = database.beginResourceSession("products");
                 final var wtx = session.beginNodeTrx()) {

                wtx.insertSubtreeAsFirstChild(JsonShredder.createStringReader("""
                    [
                      {"name": "Laptop", "price": 999},
                      {"name": "Phone",  "price": 699}
                    ]
                    """));
                wtx.commit();

                // 3. Update data (revision 2) — add a product
                wtx.moveTo(1); // move to the array node
                wtx.insertSubtreeAsFirstChild(JsonShredder.createStringReader(
                    """
                    {"name": "Monitor", "price": 349}
                    """));
                wtx.commit();
            }

            // 4. Read a specific revision
            try (final var session = database.beginResourceSession("products");
                 final var rtx = session.beginNodeReadOnlyTrx(1)) {
                // rtx is now positioned at revision 1
                final var writer = new StringWriter();
                final var serializer = new JsonSerializer.Builder(session, writer)
                    .startNodeKey(rtx.getNodeKey())
                    .revisions(new int[]{1})
                    .build();
                serializer.call();
                System.out.println("Revision 1: " + writer);
            }

            // 5. Read the latest revision
            try (final var session = database.beginResourceSession("products");
                 final var rtx = session.beginNodeReadOnlyTrx()) {
                final var writer = new StringWriter();
                final var serializer = new JsonSerializer.Builder(session, writer).build();
                serializer.call();
                System.out.println("Latest:     " + writer);
            }
        }

        // Clean up
        Databases.removeDatabase(dbPath);
    }
}
```

**Key concepts:**

- A **database** holds multiple **resources** (each is an independent versioned document)
- A **write transaction** (`JsonNodeTrx`) auto-creates a new revision on each `commit()`
- A **read-only transaction** (`JsonNodeReadOnlyTrx`) can open any historical revision
- Every past revision is immutable and permanently queryable

For the full cursor API, see [Cursor API](/docs/transactional-cursor-api.html). For the DOM-alike layer, see [DOM-alike API](/docs/dom-alike-api.html).

---

## CLI Tools

### Kotlin CLI

Build and run the Kotlin CLI for basic database operations:

```bash
git clone https://github.com/sirixdb/sirix.git
cd sirix
./gradlew :sirix-kotlin-cli:build
```

Usage:

```bash
java -jar bundles/sirix-kotlin-cli/build/libs/sirix-kotlin-cli-*-all.jar --help
```

### Interactive JSONiq shell

Launch an interactive shell to run JSONiq queries:

```bash
./gradlew :sirix-query:run
```

This opens a REPL where you can run temporal queries against local databases. See the [JSONiq Tutorial](/docs/jsoniq-tutorial.html) for query examples.

---

## What's next?

- [Features](/docs/features.html) — full feature overview
- [Architecture](/docs/architecture.html) — how SirixDB stores and versions data
- [REST API](/docs/rest-api.html) — complete endpoint reference
- [JSONiq Tutorial](/docs/jsoniq-tutorial.html) — temporal query examples
- [Use Cases](/docs/use-cases.html) — where SirixDB fits
