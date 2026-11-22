---
layout: documentation
doctitle: JSONiq Update Patterns
title: SirixDB - JSONiq Update Patterns
---

Update nested fields and array items in an order, then read the revisions SirixDB kept.

## Set up an example order

Run each JSONiq block as a separate query, in order, against the same store. Choose a fresh `update-examples` database because `jn:store` replaces a database of that name by default.

```xquery
jn:store('update-examples', 'order', '{
  "shipping": {
    "address": {"city": "Berlin", "zip": "10115"},
    "steps": ["packed", "shipped"],
    "note": "Leave at reception"
  },
  "items": [{"sku": "MUG", "qty": 1}, {"sku": "BOX", "qty": 1}]
}')
```

This stores revision 1. With the shell's default auto-commit strategy, each successful update query here creates one new revision of the order. Run the read queries separately to see the committed state. See [commit strategies](/docs/jsoniq-api.html#updating-data) if you use the Java API.

## Insert a field and add array items

Add a carrier to the nested shipping object and put `"paid"` first in its steps array. Array positions are zero-based.

```xquery
let $order := jn:doc('update-examples', 'order')
return (
  insert json {"carrier": "DHL"} into $order.shipping,
  insert json "paid" into $order.shipping.steps at position 0
)
```

Insert before an existing item by using its current index. `"packed"` is at index 1 after the preceding query.

```xquery
let $steps := jn:doc('update-examples', 'order').shipping.steps
return insert json "labeled" into $steps at position 1
```

Insert after an item by using its current index plus one. `"packed"` is now at index 2.

```xquery
let $steps := jn:doc('update-examples', 'order').shipping.steps
return insert json "scanned" into $steps at position 3
```

Use `append json` to add the last item.

```xquery
let $steps := jn:doc('update-examples', 'order').shipping.steps
return append json "delivered" into $steps
```

```xquery
let $shipping := jn:doc('update-examples', 'order').shipping
return {"carrier": $shipping.carrier, "steps": $shipping.steps}
```

```json
{
  "carrier": "DHL",
  "steps": ["paid", "labeled", "packed", "scanned", "shipped", "delivered"]
}
```

## Delete a field and an array item

Remove the shipping note and the second line item.

```xquery
let $order := jn:doc('update-examples', 'order')
return (
  delete json $order.shipping.note,
  delete json $order.items[1]
)
```

```xquery
let $order := jn:doc('update-examples', 'order')
return {"hasNote": exists($order.shipping.note), "items": $order.items}
```

```json
{"hasNote": false, "items": [{"sku": "MUG", "qty": 1}]}
```

## Replace values and rename a field

Change the quantity, replace the entire address object, and rename the quantity key inside the first line item.

```xquery
let $order := jn:doc('update-examples', 'order')
return (
  replace json value of $order.items[0].qty with 2,
  replace json value of $order.shipping.address
    with {"city": "Potsdam", "postalCode": "14467"},
  rename json $order.items[0].qty as "quantity"
)
```

The comma-separated expressions queue pending updates during evaluation. Brackit applies them at the end of the query in update-type order, and SirixDB commits all three changes together as revision 7.

## Read earlier revisions and see what changed

Pass a revision number to `jn:doc` to open an earlier snapshot. Omit it to read the latest revision.

```xquery
let $before := jn:doc('update-examples', 'order', 6)
let $after := jn:doc('update-examples', 'order')
return {
  "from": sdb:revision($before),
  "to": sdb:revision($after),
  "beforeItem": $before.items[0],
  "afterItem": $after.items[0],
  "beforeAddress": $before.shipping.address,
  "afterAddress": $after.shipping.address
}
```

```json
{
  "from": 6,
  "to": 7,
  "beforeItem": {"sku": "MUG", "qty": 1},
  "afterItem": {"sku": "MUG", "quantity": 2},
  "beforeAddress": {"city": "Berlin", "zip": "10115"},
  "afterAddress": {"city": "Potsdam", "postalCode": "14467"}
}
```

Use `jn:previous` to step back from the latest document. `sdb:timestamp` gives that revision's commit time, which you can pass to `jn:open` to read the document at that time.

```xquery
let $latest := jn:doc('update-examples', 'order')
let $previous := jn:previous($latest)
let $when := sdb:timestamp($previous)
let $atTime := jn:open('update-examples', 'order', $when)
return {
  "previous": sdb:revision($previous),
  "committedAt": string($when),
  "openedAtTime": sdb:revision($atTime)
}
```

```json
{"previous": 6, "committedAt": "2026-11-22T16:17:36.98Z", "openedAtTime": 6}
```

The timestamp comes from the commit in this run.

For a list of changes between the two snapshots, use `jn:diff`. Here the diff reports the address replacement and combines the quantity rename and value change into one update.

```xquery
jn:diff('update-examples', 'order', 6, 7)
```

```json
{
  "database": "update-examples",
  "resource": "order",
  "old-revision": 6,
  "new-revision": 7,
  "diffs": [
    {
      "replace": {
        "oldNodeKey": 3,
        "newNodeKey": 22,
        "path": "/shipping/address",
        "type": "jsonFragment",
        "data": "{\"address\":{\"city\":\"Potsdam\",\"postalCode\":\"14467\"}}"
      }
    },
    {
      "update": {
        "nodeKey": 13,
        "path": "/items/[0]/quantity",
        "name": "quantity",
        "type": "number",
        "value": 2
      }
    }
  ]
}
```
