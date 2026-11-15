---
layout: documentation
doctitle: REST API
title: SirixDB - REST API
---

[Edit this page on GitHub](https://github.com/sirixdb/sirixdb.github.io/edit/master/docs/rest-api.md)

## Overview

The SirixDB REST API is fully asynchronous, built on Vert.x and Netty. It supports both JSON and XML databases through content negotiation. Resource updates commit new revisions. Deleting a whole resource or database also removes its history.

**Local Docker base URL:** `http://localhost:9443` (`use.http: true` in the bundled Docker configuration). Configure TLS for remote deployments. The [source OpenAPI specification](https://github.com/sirixdb/sirix/blob/main/bundles/sirix-rest-api/src/main/resources/openapi.yaml) describes the current endpoint contract.

**Content negotiation:** every request must include `Content-Type` and/or `Accept` headers set to `application/json` or `application/xml`.

**Authentication:** OAuth2 via Keycloak. Obtain a token from `POST /token` and include it as `Authorization: Bearer <token>` on all subsequent requests.

**Concurrency control:** create a resource with `hashType=ROLLING` to enable node hashes (the REST default is `NONE`). For updates and subtree deletes on hashed nodes, read the response `ETag` with `HEAD` or `GET`, then send that value in `If-Match`. A missing or stale precondition returns **400**. The legacy request `ETag` header is also accepted.

---

## Authentication

### `POST /token`

Obtain or refresh an OAuth2 access token.

**Content-Type:** `application/json` or `application/x-www-form-urlencoded`

**Request body (obtain token):**

```json
{
  "username": "admin",
  "password": "admin"
}
```

**Request body (refresh token):**

```json
{
  "refresh_token": "<refresh_token>"
}
```

**Response:**

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 300
}
```

### `POST /logout`

Revoke the current access and refresh tokens.

**Request body:** the user principal JSON object returned by the authentication system.

### `GET /user/authorize`

Initiate OAuth2 Authorization Code flow (redirects to Keycloak).

| Parameter | Type | Description |
|---|---|---|
| `redirect_uri` | string | URI to redirect to after authentication |
| `state` | string | Opaque state value for CSRF protection |

---

## Databases

### `GET /` {#list-databases}

List all databases.

**Role:** `view`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `withResources` | boolean | false | Include the list of resource names per database |

**Response:**

```json
{
  "databases": [
    {
      "name": "shop",
      "type": "json",
      "resources": ["products", "customers"]
    }
  ]
}
```

### `PUT /:database` {#create-database}

Create a database. Optionally include initial resources.

**Role:** `create`

| Content-Type | Behavior |
|---|---|
| `application/json` | Create a JSON database |
| `application/xml` | Create an XML database |
| `multipart/form-data` | Create a database with multiple resources (each part specifies its own `Content-Type`) |

### `GET /:database` {#get-database}

Get database metadata and the list of all resource names.

**Role:** `view`

### `POST /:database` {#create-multiple-resources}

Create multiple resources in an existing database.

**Role:** `create`

**Content-Type:** `multipart/form-data` — each part must set its own `Content-Type` (`application/json` or `application/xml`).

### `DELETE /` {#delete-all}

Delete all databases.

**Role:** `delete`

### `DELETE /:database` {#delete-database}

Delete a database and all its resources.

**Role:** `delete`

**Content-Type:** must match the database type (`application/json` or `application/xml`).

---

## Resources

### `PUT /:database/:resource` {#create-resource}

Create a new resource with initial content. If the database does not exist, it is created automatically.

**Role:** `create`

| Parameter | Type | Description |
|---|---|---|
| `hashType` | string | `NONE` (default), `ROLLING`, or `POSTORDER`; enable hashing for optimistic concurrency |
| `commitMessage` | string | Optional commit message for the initial revision |
| `commitTimestamp` | string | Optional custom timestamp (`yyyy-MM-ddTHH:mm:ss` or `yyyy-MM-dd HH:mm:ss.SSS`, UTC). Use only when importing existing versioned data. |

**Request body:** the JSON or XML document to store.

**Example:**

```bash
curl -X PUT "http://localhost:9443/shop/products?hashType=ROLLING" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '[{"name":"Laptop","price":999},{"name":"Phone","price":699}]'
```

**Response:** small resources are serialized back; larger resources can return an empty body. Use `GET` to read the stored data.

### `GET /:database/:resource` {#get-resource}

Retrieve a resource or query it with JSONiq.

**Role:** `view`

#### Revision selection

| Parameter | Type | Description |
|---|---|---|
| `revision` | integer | Retrieve a specific revision by number |
| `revision-timestamp` | ISO datetime | Retrieve the revision closest to this timestamp (e.g. `2024-01-15T10:30:00`) |
| `start-revision` | integer | Start of a revision range |
| `end-revision` | integer | End of a revision range (inclusive) |
| `start-revision-timestamp` | ISO datetime | Start of a timestamp range |
| `end-revision-timestamp` | ISO datetime | End of a timestamp range |

#### Node selection and serialization

| Parameter | Type | Description |
|---|---|---|
| `nodeId` | long | Retrieve a specific node by its stable key |
| `withMetaData` | string | `nodeKey`, `nodeKeyAndChildCount`, or `true` for full metadata; hashes and descendant counts require hashing |
| `maxLevel` | integer | Maximum tree depth to serialize (deeper subtrees are skipped) |
| `prettyPrint` | boolean | Format the output for readability |

#### Pagination (JSON only)

| Parameter | Type | Description |
|---|---|---|
| `nextTopLevelNodes` | integer | Return the next N top-level nodes |
| `startNodeKey` | long | Continue after this node key (omit or use 0 to start) |

#### Query execution

| Parameter | Type | Description |
|---|---|---|
| `query` | string | A JSONiq expression (URL-encoded) |
| `startResultSeqIndex` | integer | Start index in the result sequence (0-based) |
| `endResultSeqIndex` | integer | End index in the result sequence (inclusive) |

**Example — retrieve revision 1:**

```bash
curl http://localhost:9443/shop/products?revision=1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

**Example — temporal query (all revisions of the root):**

```bash
curl --get "http://localhost:9443/shop/products" \
  --data-urlencode "query=jn:all-times(jn:doc('shop','products'))" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

### `HEAD /:database/:resource` {#head-resource}

Get the ETag (rolling hash) of a node. Use this before `POST` or `DELETE` operations.

**Role:** `view`

| Parameter | Type | Description |
|---|---|---|
| `nodeId` | long | Node to get the hash for |
| `revision` | integer | Specific revision |

**Response headers:**

| Header | Description |
|---|---|
| `ETag` | Rolling hash of the node (required for updates) |

### `POST /:database/:resource` {#update-resource}

Insert, replace, or modify content within a resource. Each POST creates a new revision.

**Role:** `modify`

**Precondition:** on hashed context nodes, send `If-Match` with the hash obtained from a prior `HEAD` request.

| Parameter | Type | Description |
|---|---|---|
| `nodeId` | long | Context node for the operation |
| `insert` | string | JSON: required `asFirstChild`, `asLeftSibling`, or `asRightSibling`. XML also supports `replace` (the default). |
| `commitMessage` | string | Optional commit message |
| `commitTimestamp` | string | Optional custom timestamp (UTC) |

If `nodeId` is omitted, the context is the document root’s first child. JSON insertion requires `insert`; to replace a JSON value, use a JSONiq update via `POST /`. XML defaults to replacing the context node.

**Example — insert a new product as the first child:**

```bash
# 1. Get the ETag of the array node
ETAG=$(curl -sI "http://localhost:9443/shop/products?nodeId=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | grep -i etag | tr -d '\r' | cut -d' ' -f2)

# 2. Insert a new element
curl -X POST "http://localhost:9443/shop/products?nodeId=1&insert=asFirstChild" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "If-Match: $ETAG" \
  -d '{"name":"Tablet","price":449}'
```

### `DELETE /:database/:resource` {#delete-resource}

Delete a resource or a subtree within it. Deleting the entire resource removes all of its revisions; deleting a subtree creates a new revision.

**Role:** `delete`

**Precondition:** on hashed context nodes, send `If-Match` with the hash obtained from a prior `HEAD` request.

| Parameter | Type | Description |
|---|---|---|
| `nodeId` | long | Node to delete. If it is a structure node, the entire subtree is removed. If omitted, the whole resource is deleted. |

---

## Queries

### `POST /` {#query-post}

Execute a JSONiq expression. Use this for longer or multi-line queries that are inconvenient to URL-encode.

**Role:** `view`

**Content-Type:** `application/json`

**Request body:**

```json
{
  "query": "for $rev in jn:all-times(jn:doc('shop','products')) return {\"rev\": sdb:revision($rev), \"count\": count($rev[])}",
  "startResultSeqIndex": 0,
  "endResultSeqIndex": 9
}
```

| Field | Type | Description |
|---|---|---|
| `query` | string | JSONiq expression |
| `startResultSeqIndex` | integer | Start index in result sequence (0-based) |
| `endResultSeqIndex` | integer | End index in result sequence (inclusive) |

---

## History and Diffs

### `GET /:database/:resource/history` {#history}

Get the revision history of a resource.

**Role:** `view`

**Produces:** `application/json`

| Parameter | Type | Description |
|---|---|---|
| `revisions` | integer | Return only the last N revisions |
| `startRevision` | integer | Start of revision range |
| `endRevision` | integer | End of revision range |

If no parameters are given, the full history is returned, newest first. Supply `startRevision` and `endRevision` together; do not combine this range with `revisions`.

**Response:**

```json
{
  "history": [
    {
      "revision": 1,
      "revisionTimestamp": "2024-01-15T10:30:00.000Z",
      "author": "admin",
      "commitMessage": "initial import"
    },
    {
      "revision": 2,
      "revisionTimestamp": "2024-01-15T11:00:00.000Z",
      "author": "admin",
      "commitMessage": "price update"
    }
  ]
}
```

### `GET /:database/:resource/diff` {#diff}

Compute the diff between two revisions (JSON resources only), with `1 ≤ first-revision < second-revision`.

**Role:** `view`

**Produces:** `application/json`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `first-revision` | integer | yes | The base revision |
| `second-revision` | integer | yes | The revision to compare against |
| `startNodeKey` | long | no | Restrict the diff to a subtree rooted at this node |
| `maxDepth` | long | no | Maximum depth to traverse |
| `include-data` | boolean | no | Include full subtree data for inserts (default: `false`) |

**Response:**

```json
{
  "database": "shop",
  "resource": "products",
  "old-revision": 1,
  "new-revision": 2,
  "diffs": [
    {"update": {"nodeKey": 6, "type": "number", "value": 899}},
    {"insert": {"nodeKey": 10, "insertPositionNodeKey": 1, "insertPosition": "asFirstChild", "type": "jsonFragment"}}
  ]
}
```

### `GET /:database/:resource/pathSummary` {#path-summary}

Get the path summary — a compact overview of all unique paths in the resource.

**Role:** `view`

**Produces:** `application/json`

| Parameter | Type | Description |
|---|---|---|
| `revision` | integer | Specific revision (default: latest) |

**Response:**

```json
{
  "pathSummary": [
    {"nodeKey": 1, "path": "/[]", "references": 1, "level": 1},
    {"nodeKey": 2, "path": "/{}", "references": 2, "level": 2},
    {"nodeKey": 3, "path": "/name", "references": 2, "level": 3},
    {"nodeKey": 4, "path": "/price", "references": 2, "level": 3}
  ]
}
```

---

## Temporal Navigation

### JSON: temporal functions

For JSON resources, use the `jn:` temporal functions in your JSONiq queries. Each takes a JSON item and returns it from other revisions:

| Function | Description |
|---|---|
| `jn:all-times($item)` | The item from every revision where it exists |
| `jn:first($item)` | The item in the first revision |
| `jn:last($item)` | The item in the most recent revision |
| `jn:future($item)` | All future revisions (excluding current) |
| `jn:future($item, true())` | All future revisions (including current) |
| `jn:past($item)` | All past revisions (excluding current) |
| `jn:past($item, true())` | All past revisions (including current) |
| `jn:previous($item)` | The immediately preceding revision |
| `jn:next($item)` | The immediately following revision |
| `jn:first-existing($item)` | The first revision where the item existed (was created) |
| `jn:last-existing($item)` | The last revision where the item existed (before deletion) |

Additionally, `sdb:item-history($item)` returns the item from every revision where it was inserted or modified.

**Example — track how a value changed across revisions:**

```
let $item := sdb:select-item(jn:doc('shop','products'), 6)
for $v in sdb:item-history($item)
return {"rev": sdb:revision($v), "price": $v}
```

**Example — count products in every revision:**

```
for $v in jn:all-times(jn:doc('shop','products'))
return {"rev": sdb:revision($v), "count": count($v[])}
```

### XML: temporal XPath axes

For XML resources, SirixDB provides custom XPath axes with the same semantics:

`all-time::` `first::` `last::` `future::` `future-or-self::` `past::` `past-or-self::` `previous::` `previous-or-self::` `next::` `next-or-self::`

See the [JSONiq Function Reference](/docs/jsoniq-functions.html) for the full list of temporal and inspection functions.

---

## Error Codes

| Status | Meaning |
|---|---|
| `200` | Success |
| `400` | Bad request (malformed body, missing parameters, or failed `If-Match` precondition) |
| `401` | Unauthorized (missing or invalid token) |
| `403` | Forbidden (insufficient role) |
| `404` | Database, resource, or node not found |
| `204` | Resource or subtree deleted |
| `500` | Server error |

---

## Roles

Access is controlled by Keycloak roles assigned to users or groups:

| Role | Grants |
|---|---|
| `create` | Create databases and resources |
| `view` | Read and query resources |
| `modify` | Update resources |
| `delete` | Delete databases, resources, or nodes |

Roles can be scoped to a specific database by prefixing: `shop-create`, `shop-view`, etc.

---

## Quick Setup

```bash
# Start SirixDB + Keycloak
git clone https://github.com/sirixdb/sirix.git
cd sirix
docker compose up -d

# Get a token
TOKEN=$(curl -s -X POST http://localhost:9443/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)

# Store a JSON document
curl -X PUT "http://localhost:9443/shop/products?hashType=ROLLING" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name":"Laptop","price":999},{"name":"Phone","price":699}]'

# Query it
curl "http://localhost:9443/shop/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```
