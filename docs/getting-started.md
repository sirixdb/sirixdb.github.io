---
layout: documentation
doctitle: Getting Started
title: SirixDB - Getting Started
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/getting-started.md)

Get SirixDB running and query temporal data in minutes. Pick the path that fits your use case:

| Path | Time | Best for |
|---|---|---|
| [REST API](#rest-api) | ~5 min | Building web/mobile apps, language-agnostic integration |
| [Embedded Java Library](#embedded-java-library) | ~10 min | JVM applications, maximum performance, full control |
| [CLI Tools](#cli-tools) | ~10 min | Ad-hoc queries, scripting, interactive JSONiq |

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) for the REST API path; for the embedded and CLI paths, see the [supported JVM and required launch flags](/docs/operations.html).

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

Follow the [embedded-library setup in the SirixDB README](https://github.com/sirixdb/sirix#as-an-embedded-library) for current Maven and Gradle coordinates and the command to run the example. It distinguishes the published library from source builds.

The [standalone embedded example](https://github.com/sirixdb/sirix/tree/main/docs/examples/embedded) creates an isolated temporary database, commits two revisions, and reads the original value back. Use its source and Maven configuration together.

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
