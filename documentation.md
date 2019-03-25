---
layout: documentation
doctitle: Documentation
---

## Introduction
Usually database systems simply either overwrite data in-place or do a copy-on-write operation followed by a removal of the outdated data (the latter maybe some time later from a background process). Data however naturally evolves over time. It is often times of great value to keep the history. We for instance might record the payroll of an employee at the first of march in 2019. Let's say it's 5000€ / month. Then as of 15th april we notice, that the recorded payroll was wrong and correct it to 5300€. Now, what's the answer to what the payroll was on march, first in 2019? Database Systems, which only preserve the most recent version don't even know that the payroll wasn't right. Our answer to this question depends on what source we consider most authoritative: the record or reality? The fact that they disagree effectively splits this payroll event into two tracks of time, rendering neither source entirely accurate. Questions such as these might be easily answered by temporal database systems such as Sirix. We provide at all times the system / transaction time, which is set, once a transaction commits (when is a fact valid in the database / the record). Application or valid time has to be set by the application itself (when is a fact valid in the real world/reality?).

### Data Audits
Thus, one usage scenario for Sirix is data auditing. We keep track of past revisions in our specialised index structure for (bi)temporal data and our novel sliding snapshot versioning algorithm, which balances read- and write-performance while avoiding any peaks (depending on a few options we are very space efficient and depending on the versioning algorithm we only copy changed records plus a few more during writes. Thus we for instance usually do not simply copy a whole database page if only a single record has changed; we also do not have to cluster data during every commit as in B+-trees and LSM-Trees), Furthermore, we can simply keep track of changes through hooks and our user defined secondary index structures to avoid potentially expensive diffing of whole resources (even though we can utilize hashes, which can optionally be built during update operations for integrity checks, and thus skip the comparison of whole subtree if the hashes and stable, unique node identifiers match). As already mention we can use an ID-based diff algorithm if we don't want to keep track of what changed in an additional index. We never allow to override or delete old revisions (that said we might look into how to prune old revisions if that's wanted). A single read/write transaction appends data at all times. For sure you can revert to a specific revision and commit the new revision, but all revisions in-between will be accessible for data audits. Thus, we able to help to answer who changed what and when.

### Time Travel queries
Data audits are about how specific records/nodes have changed. Time Travel queries can answer questions as these, but also allows to reconstruct a whole subtree as it looked at a specific time or during a specific time span, or how the whole document/resource changed over time. You might want to analyse the past to predict the future. Through additional temporal XPath axis and XQuery functions we encourage you to look into how your data has evolved.

### Fixing application or human errors / simple undo/redo operations
You can simple revert to a specific revision/point in time where everything was in a known good state and commit the revision again, or you might simply select a specific record/node and correct the error and commit the new revision.

### In general
Sirix is a storage system, which brings versioning to a sub-file granular level while taking full advantage of flash based drives as for instance SSDs. As such per revision as well as per page deltas are stored. Time-complexity for retrieval of records/nodes and the storage are logarithmic (`O(log n)`). Space complexity is linear (`O(n)`). Currently, we provide several APIs which are layered. A very low level page-API, which handles the storage and retrieval of records on a per page-fragment level (whereas a buffer manager handles the caching of pages in-memory and the versioning takes place even on a lower layer for storing and reconstructing the page-fragments in CPU-friendly algorithms), a cursor based API to store and navigate through records (currently XML/XDM-nodes as well as JSON-nodes) on top, a DOM-alike node layer for simple in-memory processing of these nodes, which is used by Brackit, a sophisticated XQuery processor. And last but not least a RESTful asynchronous HTTP-API. Our goal is to provide a seamless integration of a native JSON layer besides the XML node layer, that is extending the XQuery Data Model (XDM) with other node types (support for JSONiq through the XQuery processor Brackit). In general, however we could store every kind of data. We provide

1. The current revision of the resource or any subset thereof;
2. The full revision history of the resource or any subset thereof;
3. The full modification history of the resource or any subset thereof.

We not only support all XPath axis (as well as a few more like as for instance a PostOrderAxis) to query a resource in one revision but also novel temporal axis which facilitate navigation in time. A transaction (cursor) on a resource can be started either by specifying a specific revision number (to open a revision/version/snapshot of a resource) or by a given point in time. The latter starts a transaction on the revision number which was committed closest to the given timestamp.

<div class="img_container">
![sunburstview](images/sunburstview-cut.png){: style="max-width: 450px; height: auto; margin: 1.5em"} ![moves](images/moves-cut.png){: style="max-width: 450px; height: auto; margin: 1.5em"}
</div>

You may find a quick overview about the [main features](/features.) useful.

### API documentation
We provide several APIs to interact with Sirix.

1. The [transactional cursor API](/transactional-cursor-api.html) is a powerful low-level API.
2. On top of this API we built a [Brackit.org](http://brackit.org) binding to provide the ability to use Sirix with a more [DOM-alike API](/dom-alike-api.html) with in-memory nodes and an [XQuery API](/xquery-api.html).
3. We provide a powerful, asynchronous, non-blocking [RESTful-API](/rest-api.html) to interact with a Sirix HTTP-server. Authorization is done via Keycloak.  
