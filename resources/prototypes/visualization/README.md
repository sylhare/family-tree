# D3.js Visualization Prototype

A self-contained interactive family tree using D3.js v7 force-directed layout. No server or install required — just open the file in a browser.

## What it shows

- 5–6 nodes (Person + Union types) with distinct colors
- Edges labeled with relationship types (UNION, CHILD, PARENT_OF)
- Draggable nodes, zoom and pan support
- Arrow markers on directed edges

## Run

```bash
open family_tree_viz.html
```

Or double-click the file in your file manager — it loads D3.js from CDN.

## Swapping in real data

Edit the `nodes` and `links` arrays near the top of `family_tree_viz.html`:

```js
const nodes = [
  { id: "alice", label: "Alice", type: "person" },
  // ...
]

const links = [
  { source: "alice", target: "u1", label: "UNION" },
  // ...
]
```

Each node needs `id`, `label`, and `type` (`"person"` or `"union"`).
Each link needs `source`, `target` (node IDs), and `label`.
