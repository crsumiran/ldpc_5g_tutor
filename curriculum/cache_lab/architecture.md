# Cache Architecture

## Address format

All accesses are aligned 32-bit word accesses. The 8-bit byte address is divided as follows:

```text
  7       4 3     2 1     0
+----------+-------+-------+
|   tag    | index |offset |
+----------+-------+-------+
     4 bits  2 bits  2 bits
```

The index selects one of four lines. The tag identifies which memory region currently occupies that line. The offset is present because the interface is byte addressed; aligned word accesses have an offset of zero.

## Line contents

```text
line 0: valid | tag | 32-bit data
line 1: valid | tag | 32-bit data
line 2: valid | tag | 32-bit data
line 3: valid | tag | 32-bit data
```

## Policies

- Read hit: return the cached word and do not access memory.
- Read miss: request the word from memory, fill the selected line, then respond.
- Write hit: update the cached word and send the write to memory.
- Write miss: send the write to memory, but do not allocate a line.
- A memory request may stall. Keep `mem_req_valid` and its fields stable until `mem_req_ready`.
