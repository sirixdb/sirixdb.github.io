---
layout: documentation
doctitle: REST-API
title: SirixDB - REST-API
---

[Edit document on Github](https://github.com/sirixdb/sirixdb.github.io/edit/master/rest-api.md)

## Shorter Article Describing the JSON REST-API

You can find an article about this API regarding only JSON stuff on Medium: [Asynchronous, Temporal REST With Vert.x, Keycloak and Kotlin Coroutines](https://medium.com/hackernoon/asynchronous-temporal-rest-with-vert-x-keycloak-and-kotlin-coroutines-217b25756314)

## Introduction

This API is asynchronous at its very core. We use Vert.x which is a toolkit, built on top of Netty. It is heavily inspired by Node.js but for the JVM. As such it uses event loop(s), that is thread(s), which never should by blocked by long running CPU tasks or disk bound I/O. We are using Kotlin with coroutines to keep the code simple.
Authorization is done via OAuth2 (Password Credentials/Resource Owner Flow) using a Keycloak authorization server instance.

### Start Docker Keycloak-Container using docker-compose
For setting up the SirixDB HTTP-Server and a basic Keycloak-instance with a test realm:

1. `git clone https://github.com/sirixdb/sirix.git`
2. `sudo docker-compose up waitforkeycloak`

### Keycloak setup

Keycloak can be set up as described in this excellent [tutorial](
https://piotrminkowski.wordpress.com/2017/09/15/building-secure-apis-with-vert-x-and-oauth2/). Our `docker-compose` file imports a sirix realm, so basically you can skip the steps 3 - 7 and simply recreate a `client-secret` and add a user which has all the roles assigned (or an admin group with all roles and assign the user to the admin-group for running the integration tests for instance).

1. Open your browser. URL: http://localhost:8080
2. Login with username "admin", password "admin"
3. Create a new **realm** with the name **"sirixdb"**
4. Go to `Clients` => `account`
5. Change client-id to "sirix"
6. Make sure `access-type` is set to `confidential`
7. Go to `Credentials` tab
8. Put the `client secret` into the SirixDB HTTP-Server [configuration file]( https://raw.githubusercontent.com/sirixdb/sirix/master/bundles/sirix-rest-api/src/main/resources/sirix-conf.json). Change the value of "client.secret" to whatever Keycloak set up.
9. Regarding Keycloak the `direct access` grant on the settings tab must be `enabled`.
10. Our (user-/group-)roles are "create" to allow creating databases/resources, "view" to allow to query database resources, "modify" to modify a database resource and "delete" to allow deletion thereof. You can also assign `${databaseName}-` prefixed roles.
 
### Start SirixDB HTTP-Server Keycloak-Container using docker-compose
The following command will start the docker container

1. `sudo docker-compose up -d server`

### SirixDB HTTP-Server Setup Without Docker/docker-compose

To created a fat-JAR. Download our ZIP-file for instance, then

1. `cd bundles/sirix-rest-api`
2. `mvn clean package -DskipTests`

And a fat-JAR with all required dependencies should have been created in your target folder.

Furthermore, a `key.pem` and a `cert.pem` file are needed. These two files have to be in your user home directory in a directory called "sirix-data", where Sirix stores the databases. For demo purposes they can be copied from our [resources directory](https://github.com/sirixdb/sirix/tree/master/bundles/sirix-rest-api/src/main/resources).

Once also Keycloak is set up we can start the server via:

`java -jar -Duser.home=/opt/sirix sirix-rest-api-*-SNAPSHOT-fat.jar -conf sirix-conf.json -cp /opt/sirix/*`

If you like to change your user home directory to `/opt/sirix` for instance.

The fat-JAR in the future will be downloadable from the [maven repository](https://oss.sonatype.org/content/repositories/snapshots/io/sirix/sirix-rest-api/0.9.0-SNAPSHOT/).

### Run the Integration Tests
In order to run the integration tests under `bundles/sirix-rest-api/src/test/kotlin` make sure that you assign your admin user all the user-roles you have created in the Keycloak setup (last step). Then copy your generated `client secret` from step 7 in `SirixVerticleJsonTest` and `SirixVerticleXmlTest` and overwrite the one in the setup methods. Then make sure that Keycloak is running first and execute the Tests in your favorite IDE for instance.

## API-design by Example
After Keycloak and our server are up and running, we can write a simple HTTP-Client. We first have to obtain a token from the `/login` endpoint with a given "username/password" JSON-Object. Using an asynchronous HTTP-Client (from Vert.x) in Kotlin, it looks like this:

```kotlin
val server = "https://localhost:9443"

val credentials = json {
  obj("username" to "testUser",
      "password" to "testPass")
}

val response = client.postAbs("$server/token").sendJsonAwait(credentials)

if (200 == response.statusCode()) {
  val user = response.bodyAsJsonObject()
  val accessToken = user.getString("access_token")
}
```

This access token must then be sent in the Authorization HTTP-Header for each subsequent request. Storing a first resource would look like (simple HTTP PUT-Request):

```kotlin
val xml = """
    <xml>
      foo
      <bar/>
    </xml>
""".trimIndent()

var httpResponse = client.putAbs("$server/database/resource1").putHeader(HttpHeaders.AUTHORIZATION.toString(), "Bearer $accessToken").putHeader(HttpHeaders.CONTENT_TYPE.toString(), "application/xml").putHeader(HttpHeaders.ACCEPT.toString(), "application/xml").sendBufferAwait(Buffer.buffer(xml))
  
if (200 == response.statusCode()) {
  println("Stored document.")
} else {
  println("Something went wrong ${response.message}")
}
```
First, an empty database with the name `database` with some metadata is created, second the XML-fragment is stored with the name `resource1`. The PUT HTTP-Request is idempotent. Another PUT-Request with the same URL endpoint will delete the former database and resource and create the database and resource again. Note that every request has to contain an `HTTP-Header` which content type it sends and which resource-type it expects (`Content-Type: application/xml` and `Accept: application/xml`) for instance. This is needed as SirixDB supports the storage and retrieval of both XML- and JSON-data. Furthermore in case of updates as described in [Integrity Assurance for RESTful XML](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-123507) you have to make sure to include the hashCode of the node you want to modify in the "ETag" HTTP-Header. For instance if you want to insert a subtree as the first child of a node, the hashCode of the "parent" node must be in the HTTP-Header. The following sections show the API for usage with our binary and in-memory XML representation, but the JSON version is almost analogous.

The HTTP-Response should be 200 and the HTTP-body yields:

```xml
<rest:sequence xmlns:rest="https://sirix.io/rest">
  <rest:item>
    <xml rest:id="1">
      foo
      <bar rest:id="3"/>
    </xml>
  </rest:item>
</rest:sequence>
```

We are serializing the generated IDs from our storage system for element-nodes.

Via a `GET HTTP-Request` to `https://localhost:9443/database/resource1` we are also able to retrieve the stored resource again.

However, this is not really interesting so far. We can update the resource via a `POST-Request`. Assuming we retrieved the access token as before, we can simply do a POST-Request and use the information we gathered before about the node-IDs:

```kotlin
// First get the hashCode of the node with ID 3.
var httpResponse = client.headAbs("$server/database/resource1?nodeId=3")
                         .putHeader(HttpHeaders.AUTHORIZATION.toString(), "Bearer $accessToken")
                         .putHeader(HttpHeaders.CONTENT_TYPE.toString(), "application/xml")
                         .putHeader(HttpHeaders.ACCEPT.toString(), "application/xml")
                         .sendAWait()

val hashCode = httpResponse.getHeader(HttpHeaders.ETAG.toString())

val xml = """
    <test>
      yikes
      <bar/>
    </test>
""".trimIndent()

val url = "$server/database/resource1?nodeId=3&insert=asFirstChild"

httpResponse = client.postAbs(url)
                     .putHeader(HttpHeaders.AUTHORIZATION.toString(), "Bearer $accessToken")
                     .putHeader(HttpHeaders.CONTENT_TYPE.toString(), "application/xml")
                     .putHeader(HttpHeaders.ACCEPT.toString(), "application/xml")
                     .putHeader(HttpHeaders.ETAG.toString(), hashCode)
                     .sendBufferAwait(Buffer.buffer(xml))
```

The interesting part is the URL, we are using as the endpoint. We simply say, select the node with the ID 3, then insert the given XML-fragment as the first child. This yields the following serialized XML-document:

```xml
<rest:sequence xmlns:rest="https://sirix.io/rest">
  <rest:item>
    <xml rest:id="1">
      foo
      <bar rest:id="3">
        <test rest:id="4">
          yikes
          <bar rest:id="6"/>
        </test>
      </bar>
    </xml>
  </rest:item>
</rest:sequence>
```
The interesting part is that every PUT- as well as POST-request does an implicit `commit` of the underlying transaction. Thus, we are now able send the first GET-request for retrieving the contents of the whole resource again for instance through specifying an simple XPath-query, to select the root-node in all revisions `GET https://localhost:9443/database/resource1?query=/xml/all-time::*` and get the following XPath-result:

```xml
<rest:sequence xmlns:rest="https://sirix.io/rest">
  <rest:item rest:revision="1" rest:revisionTimestamp="2018-12-20T18:44:39.464Z">
    <xml rest:id="1">
      foo
      <bar rest:id="3"/>
    </xml>
  </rest:item>
  <rest:item rest:revision="2" rest:revisionTimestamp="2018-12-20T18:44:39.518Z">
    <xml rest:id="1">
      foo
      <bar rest:id="3">
        <xml rest:id="4">
          foo
          <bar rest:id="6"/>
        </xml>
      </bar>
    </xml>
  </rest:item>
</rest:sequence>
```

In general we support several additional temporal XPath axis:

`future::`, `future-or-self::`, `past::`,`past-or-self::`,`previous::`,`previous-or-self::`,`next::`,`next-or-self::`,`first::`,`last::`,`all-time::`

The same can be achieved through specifying a range of revisions to serialize (start- and end-revision parameters) in the GET-request:

```GET https://localhost:9443/database/resource1?start-revision=1&end-revision=2```

or via timestamps:

```GET https://localhost:9443/database/resource1?start-revision-timestamp=2018-12-20T18:00:00&end-revision-timestamp=2018-12-20T19:00:00```

We for sure are also able to delete the resource or any subtree thereof by an updating XQuery expression (which is not very RESTful) or with a simple `DELETE` HTTP-request:

```kotlin
// First get the hashCode of the node with ID 3.
var httpResponse = client.headAbs("$server/database/resource1?nodeId=3")
                         .putHeader(HttpHeaders.AUTHORIZATION.toString(), "Bearer $accessToken")
                         .putHeader(HttpHeaders.CONTENT_TYPE.toString(), "application/xml")
                         .putHeader(HttpHeaders.ACCEPT.toString(), "application/xml")
                         .sendAWait()

val hashCode = httpResponse.getHeader(HttpHeaders.ETAG.toString())

val url = "$server/database/resource1?nodeId=3"

val httpResponse = client.deleteAbs(url)
                         .putHeader(HttpHeaders.AUTHORIZATION.toString(), "Bearer $accessToken")
                         .putHeader(HttpHeaders.ACCEPT.toString(), "application/xml")
                         .putHeader(HttpHeaders.ETAG.toString(), hashCode).sendAwait()

if (200 == httpResponse.statusCode()) {
  ...
}
```

This deletes the node with ID 3 and in our case as it's an element node the whole subtree. For sure it's committed as revision 3 and as such all old revisions still can be queried for the whole subtree (or in the first revision it's only the element with the name "bar" without any subtree).

If we want to get a diff, currently in the form of an XQuery Update Statement (but we could serialize them in any format), simply call the XQuery function `sdb:diff`:

`sdb:diff($coll as xs:string, $res as xs:string, $rev1 as xs:int, $rev2 as xs:int) as xs:string`

For instance via a GET-request like this for the database/resource we created above, we could make this request:

`GET https://localhost:9443/?query=sdb%3Adiff%28%27database%27%2C%27resource1%27%2C1%2C2%29`

Note that the query-String has to be URL-encoded, thus it's decoded

`sdb:diff('database','resource1',1,2)`

The output for the diff in our example is this XQuery-Update statement wrapped in an enclosing sequence-element:

```xml
<rest:sequence xmlns:rest="https://sirix.io/rest">
  let $doc := sdb:doc('database','resource1', 1)
  return (
    insert nodes <xml>foo<bar/></xml> as first into sdb:select-node($doc, 3)
  )
</rest:sequence>
```

This means the `resource1` from `database` is opened in the first revision. Then the subtree `<xml>foo<bar/></xml>` is appended to the node with the stable node-ID 3 as a first child.

The following sections give a complete specification of the routes.

## API Description

The API for storing and querying XML and JSON databases are almost identical.

As described above, you first have to authenticate with a `username` and `password` and retrieve a token, which has to be sent in the Authentication header as a Bearer token:

```kotlin
val credentials = json {
  obj(
    "username" to "admin",
    "password" to "admin"
  )
}

val response = client.postAbs("$server/token").sendJsonAwait(credentials)

if (200 == response.statusCode()) {
  val user = response.bodyAsJsonObject()
  accessToken = user.getString("access_token")
}   
```

so in each request add the token: "Authorization: Bearer ${accessToken}".

### Create

In order to create a database either with multiple or a single resource:

- `POST https://localhost:9443/<database>`creates a new database. `Content-Type` will have to be `multipart/form-data` in order to create multiple resources. All resources sent in the request must be specified with a `Content-Type` of `application/xml` or `application/json`.
- `PUT https://localhost:9443/<database>/<resource>` creates a database and a resource, content being the body of the request. It must be XML or JSON. The `Content-Type` must be `application/xml` or `application/json` depending if the body of the request is XML or JSON. As it's returning the serialized form with in the case of XML additional metadata of SirixDB you should also specify the `Accept` header.

### Read

In order to get a list of all databases:
- `GET https://localhost:9443/` serializes all database names and types. For instance:

  ```json
  {"databases":[{"name":"json-database","type":"json"},{"name":"xml-database","type":"xml"}]}
  ```

In order to view database contents:
- `GET https://localhost:9443/<database>` serializes the database name and all resource names in the database

In order to query a resource in a database:
- `GET https://localhost:9443/<database>/<resource>` simply serializes the internal binary tree representation back to XML or JSON. Optional URL-parameters are

  - `revision`  or `revision-timestamp` (the former being a simple long number, the latter being an ISO formatted datetime string as the parameter, for instance `2019-01-01T05:05:01`), to open a specific revision. In case of the `revision-timestamp`parameter either the exact revision is going to be selected via binary search, or the closest revision to the given point in time.
  - `start-revision` and `end-revision` or `start-revision-timestamp` and `end-revision-timestamp` for a specific timespan.
  - Furthermore a `nodeId`-parameter can be specified to retrieve a specific node in a revision.
  - The `query`-parameter can be used to specify a full blown XQuery-string. Here for instance also temporal axis can be used to analyze how a specific node or subtree changed over time or to display which nodes are new in a specific revision. There's also a `diff`-function which outputs an XQuery Update script to update the first revision to the second. Other formats as output to another diff-function are for sure have to be evaluated.
  - When you're specifying a `query`-parameter you can also add two other parameters: `startResultSeqIndex` and `endResultSeqIndex` to specify the start index of when to deliver results from the result sequence starting from 0 and an optional end index (inclusive).

### Update

In order to update or delete a resource stored in a database you have to make sure to specify the `Content-Type` (`application/xml` or `application/json`). Furthermore you have to get the hashcode for the context-node first, for instance with either a GET-request as shown above or a HEAD-request against the resource with an optional `revision`-parameter and a `nodeId`-parameter. The hashcode will be sent in the `ETag` HTTP-response header. You have to set it in your `Etag` HTTP-request header, too. As it is a rolling hash to cover whole subtrees in resources, SirixDB is then able to detect concurrent modifications between the time a client has made a reading request and an updating request and thus will throw an excption and the client has to re-read the context-node of the update operation.

- `POST https://localhost:9443/<database>/<resource>` for adding content from the request-body. Supported URL-parameters are
  - `nodeId`, to select the context-Node.
  - `insert` with the possible values, `asFirstChild`, `asLeftSibling`, `asRightSibling`, `replace`, to determine where to insert the XML-fragment or the JSON data (**note that for JSON asLeftSibling is not supported as of now**).

If both parameters are omitted the root-node (and its subtree) is going to be replaced by the new XML fragment or JSON data. In the case of XML an error is thrown if the HTTP request body doesn't start with a start-tag.

- `POST https://localhost:9443`: send longer XQuery-expression in the body. For instance
```json
{ 
  "query": "//foo/bar",
  "startResultSeqIndex": 3,
  "endResultSeqIndex: 5
}
```

### Delete

- `DELETE https://localhost:9443` removes all databases stored. No `Content-Type` declaration is needed.
- `DELETE https://localhost:9443/<database>` removes the database with all resources. You have to speficy the `Content-Type` depending if the $database is of type JSON or XML (`application/xml` or `application/json`).
- `DELETE https://localhost:9443/<database>/<resource>` removes the resource from the database. Omitting the resource in the URL, the whole database is going to be deleted. The optional parameter once again is `nodeId` to remove a node or in case the nodeId references an element node to remove the whole subtree and the element node itself.
