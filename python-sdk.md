---
layout: documentation
doctitle: Python SDK API
title: SirixDB - Python SDK API
---

## Introduction

The python SDK for provides a simple, intuitive API for accessing the SirixDB REST-API. It can be used both with synchronous code, or with asynchronous code.

This document is a tutorial for using the python SDK (henceforth: pysirix), including setting up SirixDB locally using docker.

This document concentrates on JSON data, but much of it valid with XML data as well.

The API docs can be found [here](https://pysirix.readthedocs.io/).

## Setting up SirixDB locally

Unfortunately, this is currently a bit messy, but still rather straightforward.

There are several resources required to run SirixDB, and they can all be found [here](https://github.com/sirixdb/sirix-python-client/tree/master/tests/resources).

SirixDB depends on keycloak for authentication, so we first need to run (in the directory in which you have the above resources):

```bash
docker-compose up -d keycloak
```

It can take about a minute for keycloak to be ready for connections. If you like, you can use the `wait.sh` script in the above mentioned resources folder to wait until keycloak is ready. The docker-compose file runs a script from the resources folder to initialize keycloak with a user "admin" with the password "admin".

Once keycloak is ready, run:

```bash
docker-compose up -d server
```

The Sirix database is now ready for use.

## Getting started with `pysirix`

First, let's install `pysirix`:

```bash
pip install pysirix
```

`pysirix` uses the [`httpx`](https://www.python-httpx.org/) library, and the low level `resource` interface is actually a this wrapper around `httpx` and pysirix requires you to initialize the httpx client directly:

If you use https


```python
>>> import pysirix
>>> import httpx

>>> client = httpx.Client(base_url="https://localhost:9443", verify=<path/to/cert.pem/in/resources/folder>)
>>> sirix = pysirix.sirix_sync("admin", "admin", client)
```
Else use this

```python
>>> import pysirix
>>> import httpx

>>> client = httpx.Client(base_url="http://localhost:9443")
>>> sirix = pysirix.sirix_sync("admin", "admin", client)
```

You can change the setting in Sirix core repository `/sirixdb/sirix`

`/bundles/sirix-rest-api/src/main/resources/sirix-docker-conf.json`

And also find the cert.pem file here

`/bundles/sirix-rest-api/src/main/resources/cert.pem`

We now have a `Sirix` class instance, from which we can start interfacing with the database.

This is also where the only under-the-hood operation occurs in pysirix. The `sirix_sync` function calls `sirix.authenticate()`, which both retrieves an access token (using the first two parameters to `sirix_sync` as username and password), and starts a thread to periodically refresh that access token.

Should you want to use the asynchronous version of pysirix, you can run the REPL using IPython or (with python 3.8) `python -m asyncio`, and do the following:

```python
>>> import pysirix
>>> import httpx

>>> client = httpx.AsyncClient(base_url="https://localhost:9443", verify=<path/to/cert.pem/in/resources/folder>)
>>> sirix = await pysirix.sirix_async("admin", "admin", client)
```

In async mode, any method that will do a network request must be awaited, while any method that returns a pysirix object should not be awaited (excepting the `sirix_async` function). The rest of this tutorial will use async mode, to make it obvious which methods are doing network requests, and which are not.

## Creating databases and resources

```python
>>> from pysirix import DBType

>>> db = sirix.database("test-json-database", DBType.JSON)
```

We now have a database object, of database-type JSON, but it doesn't exist on the server yet.
For that we need to call the create method:

```python
>>> await db.create()
```

Generally, however, it is unnecessary to explicitly create a database, as it will be created implicitly when a resource belonging to it is created. Like so:

```python
>>> resource = db.resource("test-json-resource")
>>> await resource.create([])
'[]'
```

The create method needs some data with which to instantiate the resource, so we have passed in an array. Alternatively, you could pass in a dictionary, or stringified JSON.

Alternatively, if you were creating an XML resource, you would pass in an instance of `xml.etree.ElementTree.Element`, or strigified XML.

The array we passed in is empty, but this is arbitrary. We could, for example, do the following:

```python
>>> await resource.create(["blah", {"a key": 5}])
'["blah",{"a key":5}]'
```

Something to keep in mind is that calling `resource.create()` on an existing resource *will overwrite* any previous data in the resource. So, before calling `resource.create()`, it is good practice to call:

```python
>>> await resource.exists()
True
```

Where the `exists` variable is a `bool`, indicating whether or not the resource already exists.

There are other ways of getting information on existing databases and resources. For example, to retrieve the names of all resources associated with the current database, we can call:

```python
>>> await db.get_database_info()
{'resources': ['test-json-resource']}
```

Or, if we want the names of all databases, we can call:

```python
>>> await sirix.get_info()
[{'name': 'test-json-database', 'type': 'json', 'resources': ['test-json-resource']}]
```

As we can see, this returns a list of dictionaries, where each dictionary has the keys `"name"`, `"type"`, and `"resources"`.

If we aren't interested in the resources, and want only the database names and types, we can call:

```python
>>> await sirix.get_info(False)
[{'name': 'test-json-database', 'type': 'json'}]
```

## Manipulating resources

### Read resource data

Let us now read the resource from the SirixDB server:

```python
>>> await resource.read(None)
['blah', {'a key': 5}]
```

Normally, we pass in the nodeId of the (root of the) nodes we want to read. But since we want to read the entire file, we passed in `None` instead. Passing in `0` or `1` would have the same effect.

Let's read some particular nodes:

```python
>>> await resource.read(2)
'blah'
>>> await resource.read(3)
{'a key': 5}
```

There are more parameters that can be passed to `resource.read()`, and we will come back to them later.

### Updating resource data

Let us update some data:

```python
>>> await resource.update(1, {})
'[{},"blah",{"a key":5}]'
```

Now, there are actually more parameters needed for an update, but the rest of them are filled in under the hood if you don't provide them. So, what is going on under the hood is equivalent of:

```python
>>> from pysirix import Insert
>>> etag = await resource.get_etag(1)
>>> await resource.update(1, {}, etag=etag, insert=Insert.CHILD)
'[{},{},"blah",{"a key":5}]'
```

The Insert class is an `Enum` with the following options:

```python
class Insert(enum.Enum):
    """
    This Enum class defines the possible options for a resource update
    """

    CHILD = "asFirstChild"
    LEFT = "asLeftSibling"
    RIGHT = "asRightSibling"
    REPLACE = "replace"
```

The utility of the `etag` parameter, is that if the node was modified between the retrieval of the etag and the update, the server (and in turn, pysirix) will raise an error. This is especially useful if you already have the etag; you can provide the etag to the `update` method, and if you get an error, you know that you need to refresh your data, and decide if you still want to perform the update (in which case you will need the new etag).

Let's insert a more complex object:

```python
>>> await resource.update(1, {"hey": "test"}, insert=Insert.CHILD)
'[{"hey":"test"},{},{},"blah",{"a key":5}]'
```

### Reading metadata

To read metadata, we can call the ``read_with_metadata()`` method, which takes the same parameters as read(). Let's call it for the initial state of the resource:

```python
>>> resource.read_with_metadata(None, revision=1)
{'metadata': {'nodeKey': 1, 'hash': 208557195544488990616803682550450165186, 'type': 'ARRAY', 'descendantCount': 4, 'childCount': 2}, 'value': [{'metadata': {'nodeKey': 2, 'hash': 288368958454372192948750575366137138081, 'type': 'STRING_VALUE'}, 'value': 'blah'}, {'metadata': {'nodeKey': 3, 'hash': 180526408181230893715743363206931647349, 'type': 'OBJECT', 'descendantCount': 2, 'childCount': 1}, 'value': [{'key': 'a key', 'metadata': {'nodeKey': 4, 'hash': 126324580879345353515887406488057081359, 'type': 'OBJECT_KEY', 'descendantCount': 1}, 'value': {'metadata': {'nodeKey': 5, 'hash': 1390911141598899303029604730715488514, 'type': 'OBJECT_NUMBER_VALUE'}, 'value': 5}}]}]}
```

The structure of the metadata returned is of type ``MetaNode``, and is a bit complex. See the API docs for details. If you are using python 3.8+, then you can use ``MetaNode`` as a type hint in your code.


### The history of the resource

We can get a list of the commits/revisions of this resource with the ``history()`` method:

```python
>>> await resource.history()
[{'revision': 4, 'revisionTimestamp': '2020-05-06T15:50:16.944Z', 'author': 'admin', 'commitMessage': ''}, {'revision': 3, 'revisionTimestamp': '2020-05-06T15:40:16.675Z', 'author': 'admin', 'commitMessage': ''}, {'revision': 2, 'revisionTimestamp': '2020-05-06T15:40:01.932Z', 'author': 'admin', 'commitMessage': ''}, {'revision': 1, 'revisionTimestamp': '2020-05-06T15:37:57.880Z', 'author': 'admin', 'commitMessage': ''}]
```

Commits are ordered from most recent to least recent.

### Differentials

We can obtain the differences between revisions as follows:

```python
>>> await resource.diff(3,4)
[{'insert': {'nodeKey': 8, 'insertPositionNodeKey': 1, 'insertPosition': 'asFirstChild', 'deweyID': '1.3.2.2.2.3', 'depth': 2, 'type': 'jsonFragment', 'data': '{"hey":"test"}'}}]
```

### Deleting a node

Finally, we can delete a node:

```python
>>> await resource.delete(8, None)
>>> await resource.read(None)
[{}, {}, 'blah', {'a key': 5}]
```

The first argument to ``delete()`` is the nodeKey, and the second is the etag. If the etag is ``None``, ``pysirix`` will retrieve it and provide it under the hood.

We can also delete the entire resource by specifying ``None`` as both arguments:

```python
>>> await resource.delete(None, None)
>>> await resource.exists()
False
```

## Using the JsonStore abstraction

`pysirix` provides a convenient interface for storing records in SirixDB.

```python
>>> json_store = db.json_store("json-store")
>>> await json_store.create()
'[]'
>>> await json_store.exists()
True
```

The `JsonStore` create an array to store records in, which is why it returns `[]`.

```python
>>> await json_store.insert_one({"key1": "foo", "key2": "bar"})
'[{"key1":"foo","key2":"bar"}]'
>>> await json_store.insert_one({"key1": "bar", "key2": "foo"})
'[{"key1":"bar","key2":"foo"},{"key1":"foo","key2":"bar"}]'
>>> await json_store.insert_one({"key1": "bar", "key2": "foo"})
'[{"key1":"bar","key2":"foo"},{"key1":"bar","key2":"foo"},{"key1":"foo","key2":"bar"}]'
```

We can query for matching records using `find_all()`:

```python
>>> await json_store.find_all({"key1": "foo"})
{'rest': [{'key1': 'foo', 'key2': 'bar', 'nodeKey': 2}]}
>>> await json_store.find_all({"key1": "bar"})
{'rest': [{'key1': 'bar', 'key2': 'foo', 'nodeKey': 12}, {'key1': 'bar', 'key2': 'foo', 'nodeKey': 7}]}
```

By default, `pysirix` also includes the nodeKey of the record root, you can control this behavior by passing `node_key=False` to `find_all()`.

It is also possible to project record results, so only certain fields are returned from matching records:

```python
>>> await json_store.find_all({"key1": "bar"}, ["key2"])
{'rest': [{'key2': 'foo', 'nodeKey': 12}, {'key2': 'foo', 'nodeKey': 7}]}
```

We can also choose which revision we query, using the `revision` parameter:

```python
>>> await json_store.find_all({"key1": "bar"}, revision=3)
{'rest': [{'key1': 'bar', 'key2': 'foo', 'nodeKey': 7}]}
```

There is only one result, as only one matching record existed in revision 3.

The `JsonStore` is still not finished, so only these methods have been implemented so far.
