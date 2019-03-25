---
layout: documentation
doctitle: Features
---

### Features in a nutshell
1. Currently native XML and JSON storage (other data types might follow),
2. Transactional, versioned, typed user-defined index-structures, which are automatically updated once a transaction commits.
3. Through XPath-axis extensions we support the navigation not only in space but also in time (future::, past::, first::, last::...). Furthermore we provide several temporal XQuery functions due to our integral versioning approach. Temporal navigation for JSON resources is done via builtin XQuery functions.
4. An in memory path summary, which is persisted during a transaction commit and always kept up-to-date.
5. Configurable versioning at the database level (full, incremental, differential and a new sliding snapshot algorithm which balances reads and writes without introducing write-peaks, which are usually generated during intermediate full dumps, which are usually written to).
6. Log-structured sequential writes and random reads due to transactional copy-on-write (COW) semantics. This offers nice benefits as for instance no locking for concurrent reading-transactions and it takes full advantage of flash disks while avoiding their weaknesses.
7. Complete isolation of currently N read-transactions and a single write-transaction per resource.
8. The page-structure is heavily inspired by ZFS and therefore also forms a tree. We'll implement a similar merkle-tree and store hashes of each page in parent-pointers for integrity checks.
9. Support of XQuery and XQuery Update due to a slightly modified version of brackit(.org).
10. Moves for the XML layer are additionally supported.
11. Automatic path-rewriting of descendant-axis to child-axis if appropriate.
12. Import of differences between two XML-documents, that is after the first version of an XML-document is imported an algorithm tries to update the Sirix resource with a minimum of operations to change the first version into the new version.
13. A fast ID-based diff-algorithm which is able to determine differences between any two versions of a resource stored in Sirix optionally taking hashes of a node into account.
14. The number of children of a node, the number of descendants, a hash as well as an ORDPATH / DeweyID label which is compressed on disk to efficiently determine document order as well as to support other nice properties of hierarchical node labels is optionally stored with each node. Currently the number of children is always stored and the number of descendants is stored if hashing is enabled.
15. Flexible backend.
16. Optional encryption and/or compression of each page on disk.
