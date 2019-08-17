---
layout: documentation
doctitle: Documentation
---

[Go directly to the API documentation](#api-documentation) or [to the publications](#publications).

## Introduction
Usually, database systems simply either overwrite data in-place or do a copy-on-write operation followed by the removal of the outdated data. The latter may be some time later from a background process. Data however naturally evolves. It is oftentimes of great value to keep the history of our data. We, for instance, might record the payroll of an employee on the first of March in 2019. Let's say it's 5000€ / month. Then as of 15th April, we notice, that the recorded payroll was wrong and correct it to 5300€. Now, what's the answer to what the payroll was on March, first in 2019? Database Systems, which only preserve the most recent version don't even know that the payroll wasn't right. Our answer to this question depends on what source we consider most authoritative: the record or reality? The fact that they disagree effectively splits this payroll event into two tracks of time, rendering neither source entirely accurate. Questions such as these might be easily answered by temporal database systems such as SirixDB. We provide at all times the transaction time, which is set, once a transaction commits (when is a fact valid in the database / the record). Application or valid time has to be set by the application itself (when is a fact valid in the real world/reality?).

### Data Audits
Thus, one usage scenario for SirixDB is data auditing. We keep track of past revisions in our specialized index structure for (bi)temporal data and our novel sliding snapshot versioning algorithm, which balances read- and write-performance while avoiding any peaks (our system is very space-efficient and depending on the versioning algorithm we only copy changed records plus maybe  a few more during writes). Thus we for instance usually do not simply copy a whole database page if only a single record has changed; we also do not have to cluster data during every commit as in B+-trees and LSM-Trees), Furthermore, we can simply keep track of changes through hooks and our user-defined secondary index structures to avoid potentially expensive diffing of whole resources (even though we can utilize hashes, which can optionally be built during update operations for integrity checks, and thus skip the comparison of the whole subtree if the hashes and stable, unique node identifiers match). As already mentioned we can use an ID-based diff algorithm if we do not want to keep track of what changed in an additional index. We never allow to override or delete old revisions (that said we might look into how to prune old revisions if that is ever needed). A single read-write transaction appends data at all times. For sure we can revert a resource to a specific revision and commit the new revision. All revisions in-between will be accessible for data audits. Thus, SirixDB can support answering questions such as who changed what and when.

### Time Travel queries
Data audits are about how specific records have changed. Time Travel queries can answer questions like these. However, they also allow reconstructing records as they looked at a specific time or during a specific period. They also help us to analyse how the whole document changed over time. We might want to analyze the past to predict the future. Through additional temporal XPath axes and XQuery functions SirixDB encourages you to look into how your data has evolved.

### Fixing application or human errors / simple undo/redo operations / rollbacks / reproduce experiments
For all of the above-mentioned use cases: We can simply revert to a specific revision/point in time where everything was in a known good state and commit the revision again, or we might simply select a specific record and correct the error and commit the new revision.

### In general
SirixDB is a storage system, which brings versioning to a sub-file granular level while taking full advantage of flash-based drives as SSDs. As such per revision as well as per page deltas are stored. Time-complexity for retrieval of records and the storage are logarithmic (`O(log n)`). Space complexity is linear (`O(n)`). Currently, we provide several APIs which are layered. A very low-level page-API, which handles the storage and retrieval of records on a per page-fragment level.  A transactional cursor-based API to store and navigate through records (currently XML as well as JSON nodes) on top. A DOM-alike node layer for simple in-memory processing of these nodes, which is used by Brackit, a sophisticated XQuery processor. And last but not least a RESTful asynchronous HTTP-API. We provide

1. The current revision of the resource or any subset thereof;
2. The full revision history of the resource or any subset thereof;
3. The full modification history of the resource or any subset thereof.

We not only support all XPath axes to query a resource in one revision but also temporal axes which facilitate navigation in time. A transactional cursor on a resource can be started either by specifying a specific revision number or by a given point in time. The latter starts a transaction on the revision number which was committed closest to the given timestamp.

<div class="img_container">
![sunburstview](images/sunburstview-cut.png){: style="max-width: 450px; height: auto; margin: 1.5em"} ![moves](images/moves-cut.png){: style="max-width: 450px; height: auto; margin: 1.5em"}
</div>

You may find a quick overview about the [main features](/features.html) useful.

### API documentation
We provide several APIs to interact with SirixDB.

1. The [transactional cursor API](/transactional-cursor-api.html) is a powerful low-level API.
2. On top of this API we built a [Brackit.org](http://brackit.org) binding to provide the ability to use SirixDB with a more [DOM-alike API](/dom-alike-api.html) with in-memory nodes and an [XQuery API](/xquery-api.html).
3. We provide a powerful, asynchronous, non-blocking [RESTful-API](/rest-api.html) to interact with a SirixDB HTTP-server. Authorization is done via Keycloak.

### Publications
Articles published on Baeldung:
- [A Guide to SirixDB](https://www.baeldung.com/sirix)

Articles published on Medium: 
- [Asynchronous, Temporal  REST With Vert.x, Keycloak and Kotlin](https://medium.com/hackernoon/asynchronous-temporal-rest-with-vert-x-keycloak-and-kotlin-coroutines-217b25756314)
- [Pushing Database Versioning to Its Limits by Means of a Novel Sliding Snapshot Algorithm and Efficient Time Travel Queries](https://medium.com/sirixdb-sirix-io-how-we-built-a-novel-temporal/why-and-how-we-built-a-temporal-database-system-called-sirixdb-open-source-from-scratch-a7446f56f201)
- [How we built an asynchronous, temporal RESTful API based on Vert.x, Keycloak and Kotlin/Coroutines for Sirix.io (Open Source)](https://medium.com/sirixdb-sirix-io-how-we-built-a-novel-temporal/how-we-built-an-asynchronous-temporal-restful-api-based-on-vert-x-4570f681a3)
- [Why Copy-on-Write Semantics and Node-Level-Versioning are Key to Efficient Snapshots](https://hackernoon.com/sirix-io-why-copy-on-write-semantics-and-node-level-versioning-are-key-to-efficient-snapshots-754ba834d3bb)

SirixDB was forked from Treetank (which is not maintained anymore), but as a university project, it was subject to some publications.

A lot of the ideas still are based on the Ph.D. thesis of Marc Kramis: [Evolutionary Tree-Structured Storage: Concepts, Interfaces, and Applications](http://www.uni-konstanz.de/mmsp/pubsys/publishedFiles/Kramis2014.pdf)

As well as from Sebastian Graft's work and thesis: [Flexible Secure Cloud Storage](https://kops.uni-konstanz.de/handle/123456789/27250)

Other publications include:

- [Versatile Key Management for Secure Cloud Storage](http://nbn-resolving.de/urn:nbn:de:bsz:352-200971) (DISCCO12) 
- [A legal and technical perspective on secure cloud Storage](http://nbn-resolving.de/urn:nbn:de:bsz:352-192389) (DFN Forum12) 
- [A Secure Cloud Gateway based upon XML and Web Services](http://nbn-resolving.de/urn:nbn:de:bsz:352-154112) (ECOWS11, PhD Symposium)
- [Treetank, Designing a Versioned XML Storage](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-126912) (XMLPrague11)
- [Hecate, Managing Authorization with RESTful XML](http://nbn-resolving.de/urn:nbn:de:bsz:352-126237) (WS-REST11)
- [Rolling Boles, Optimal XML Structure Integrity for Updating Operations](http://nbn-resolving.de/urn:nbn:de:bsz:352-126226) (WWW11, Poster)   
- [JAX-RX - Unified REST Access to XML Resources](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-120511) (TechReport10)
- [Integrity Assurance for RESTful XML](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-123507)  (WISM100) 
- [Temporal REST, How to really exploit XML](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-84476) (IADIS WWW/Internet08)
- [Distributing XML with focus on parallel evaluation](http://nbn-resolving.de/urn:nbn:de:bsz:352-opus-84487) (DBISP2P08)
