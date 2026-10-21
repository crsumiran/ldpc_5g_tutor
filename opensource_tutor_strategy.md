# Open Source Ecosystem Strategy: Verilog Tutor

This document outlines the architecture, setup, and core system prompt for building the Verilog Tutor using open-source agentic frameworks (like OpenHands or AutoGen) paired with OpenRouter or local models (like Hermes).

## 1. Architecture Overview
**The DIY / Open Framework Approach:** This provides maximum flexibility and avoids ecosystem lock-in, allowing you to swap LLMs at will.
*   **The Brain:** OpenRouter API (for Claude/GPT/Llama) or a local instance of Hermes (via Ollama/vLLM).
*   **The Engine:** Microsoft AutoGen (for multi-agent routing) OR OpenHands (for an out-of-the-box coding sandbox). 
*   **The Sandbox:** A Docker container managed by your Engine, pre-installed with `iverilog` and `verilator`.
*   **Frontend:** A standalone React/Next.js app that interfaces with your Engine's API.

## 2. Multi-Agent Framework (AutoGen Strategy)
Using a framework like AutoGen, we define two distinct agents that talk to each other to process the student's work.

### Agent A: The Verilog Executor (Code execution only)
*   **Role:** Takes Verilog code, saves it to the sandbox, runs `iverilog`, and returns the raw terminal output.
*   **Tools:** `write_file`, `execute_bash`.

### Agent B: The Socratic Tutor (User-facing)
*   **Role:** Communicates with the student. Sends code to Agent A for verification, analyzes the results, and writes the pedagogical response.

## 3. The System Prompt (Tutor Agent)

```text
You are an expert FPGA Engineer and a Socratic Verilog tutor. Your goal is to help the student learn without giving them the final answers.

# Rules of Engagement
1. **No Direct Solutions:** Never write the correct code for the student. If they ask for the answer, politely decline and provide a conceptual hint instead.
2. **Utilize the Executor:** When the student submits an assignment, you must hand the code over to the 'Verilog Executor' agent. Wait for its terminal output report.
3. **Analyze and Hint:** Review the compiler errors or simulation mismatch from the Executor. Formulate your response based on this data. For example: "The compiler found a syntax error on line 14. Remember the difference between blocking (=) and non-blocking (<=) assignments in sequential logic."
4. **Curriculum:** Follow the predefined curriculum. Do not move to the next topic until the student's code successfully compiles and passes the testbench.

# Tone
Encouraging, strictly pedagogical, and technical.
```

## 4. Brainstorming Questions for this Session
*   Which open-source framework best fits our needs: OpenHands (easier sandbox) or AutoGen (better multi-agent conversation)?
*   If we use local Hermes, do we have enough local GPU VRAM to run a model smart enough for Verilog?
*   How do we handle malicious code execution in the Docker sandbox if this is deployed to the public?
