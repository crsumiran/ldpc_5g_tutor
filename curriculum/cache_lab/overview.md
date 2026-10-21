# Build a Direct-Mapped Cache

This lab turns a small cache into a sequence of experiments. You will implement one hardware idea at a time, compile it, observe its signals, and then connect it to the next block.

The finished design is an 8-bit byte-addressed, direct-mapped cache with four lines. Each line stores one 32-bit word. Reads use **read allocate**. Writes use **write through** and **no write allocate**.

## How to work

1. Read the goal and interface contract in each checkpoint.
2. Make the smallest implementation that satisfies the contract.
3. Use **Compile & Elaborate** for wiring and syntax feedback.
4. Use **Run Public Tests** for formative behavior feedback.
5. Submit only after you can explain why the visible tests pass.

The tutor can help interpret a compiler diagnostic or failed test, but it will not provide a complete drop-in module.
