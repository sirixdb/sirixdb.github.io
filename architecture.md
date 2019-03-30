---
layout: documentation
doctitle: Architecture
---

## Introduction
Sirix is a temporal database system and never overwrites data. Let's first define what a temporal database system is all about.

It is a term used to describe, that a system is capable of retrieving past states of your data. Typically a temporal database stores both valid time, how long a fact is true in the real world as well as transaction time, when the data actually is committed to the database.

Questions such as: Give me last month’s history of the Dollar-Pound Euro exchange rate. What was the customers address on July 12th in 2015 as it was recorded back in the day? Did they move or did we correct an error? Did we have errors in the database, which were corrected later on?

Let’s turn or focus to the question why historical data hasn’t been retained in the past and how new storage advances in recent years made it possible, to build sophisticated solutions to help answer these questions without the hurdle, state-of-the-art systems bring.

## Advantages and disadvantages of flash drives as for instance SSDs
As Marc Kramis points out in his paper “Growing Persistent Trees into the 21st Century”:

> The switch to flash drives keenly motivates to shift from the “current state’’ paradigm towards remembering the evolutionary steps leading to this state.

The main insight is that flash drives as for instance SSDs, which are common nowadays have zero seek time while not being able to do in-place modifications of the data. Flash drives are organized into pages and blocks. Due to their characteristics they are able to read data on a fine-granular page-level, but can only erase data at the coarser block-level. Blocks first have to be erased, before they can be updated. Thus, updated data first is written to another place. A garbage collector marks the data, which has been rewritten to the new place as erased at the old block, such that new data can be stored in the future. Furthermore index-structures are updated.

Evolution of state through fine grained modifications
Furthermore Marc points out, that small modifications, because of clustering requirements due to slow random reads of traditionally mechanical disk head seek times, usually involves writing not only the modified data, but also all other records in the modified page as well as a number of pages with unmodified data. This clearly is an undesired effect.

## How we built an Open Source storage system based on these observations from scratch

Sirix stores per revision and per page-deltas. Due to zero seek time of flash drives we do not have to cluster data. Sirix only ever clusters data during transaction commits. It is based on an append-only storage. Data is never modified in-place.

Instead, it is copied and appended to a file in a post-order traversal of the internal tree-structure in batches once a transaction commits.

The page-structure for one revision is depicted in the following figure:

<div class="img_container">
![pageStructure](images/pageStructureOneRev.png){: style="max-width: 100%; height: auto; margin: 0em"}
</div>

The `UberPage` is the main entry point. It contains header information about the configuration of the resource as well as a reference to an `IndirectPage`. A reference contains the offset of the IndirectPage in the data-file or the transaction-intent log and an in-memory pointer. IndirectPages are used to increase the fanout of the tree. We currently store 512 references in the `IndirectPage` to either another layer of indirect pages or the data pages, either a `RevisionRootPage` or a `RecordPage`. A new level of indirect pages is added whenever we run out of the number of records we can store in the leaf pages (either revisions or records), which are referenced by the `IndirectPage`s. The height of the current subtree, that is the number of levels of indirect pages is always stored in the respective subtree-root page.

We borrowed the ideas from the filesystem ZFS and hash-array based tries as we also store checksums in parent database-pages/page-fragments, which in turn form a self-validating merkle-tree.

As IndirectPages may have many `null`-pointers we use a bitset to keep track of which array indices are really set and thus are able to store a compact array or list in-memory.

The `RevisionRootPage` is the main entry point to a revision. It stores the author-ID, an optional commit-message and a timestamp in the form of the unix epoch (milliseconds since 1970). Furthermore it stores a reference to a `PathPage`, a `CASPage` (if it exists), a `NamePage` and an `IndirectPage`. The indirect page is the entry point to the data stored in the leaf `RecordPage`s. The `PathPage` has a reference to a `PathSummary` page, which in its subtree stores a lightweight path summary in the linked `RecordPage`s. Other references to indirect pages are added, once path indexes are created. Each path index has a unique number which also denotes which reference to use. The `NamePage` contains dictionaries of frequently used names (element-names/attribute-names in XML or object key names in JSON), which are referenced from the records. Furthermore `IndirectPage`s are created once Name-indexes are created, whereas each indirect page then is the root to the index. Just like CAS (content-and-structure) and path-indexes an AVL-tree is stored in the record-pages. `CASPages` are the subtree root to these so called content-and-structure indexes. They are a hybrid consisting of path class definitions and typed content, for instance `/book/published[xs:dateTime]` indexes the path `/book/published` and the content as `xs:dateTime`.

The right subtree of the `RevisionRootPage` started by the `IndirectPage` actually is the main entry point to our data stored in the leaf nodes, the `RecordPage`s once again.

To support fast access to a RevisionRootPage we store a second file with just the offsets to specific revisions in a revisions-file, which is read into main-memory on startup.

In order to support the efficient storage/retrieval of small and large records we introduced `OverflowPage`s for large records, which only have to be read, if they are directly selected, as we usually store byte-arrays and once deserialized the reconstructed instances in in-memory maps.

<div class="img_container">
![pageStructure](images/copy-on-write.png){: style="max-width: 100%; height: auto; margin: 0em"}
</div>

