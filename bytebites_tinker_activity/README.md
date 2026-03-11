# TF Reflection: Engineering with an AI Partner

## Overview

This activity was less about writing Python code from scratch and more about mastering the role of an **AI Orchestrer**. By building the ByteBites backend, I practiced how to strategically use generative tools to move from a vague concept to a verified, functional system.

## Reflection on the AI-Assisted Workflow

### 1. From Ambiguity to Architecture

The most critical step wasn't coding; it was **defining intent**. By translating the "Client Feature Request" into core candidate classes, I provided the necessary constraints for the AI to be effective.

* **Insight:** I learned that AI performance scales with the quality of context. Using a spec file (`bytebites_spec.md`) as a "source of truth" prevented the AI from drifting into irrelevant features.

### 2. Guardrails via Custom Agents

Configuring the **ByteBites Design Agent** was a turning point. Instead of repeating my requirements in every chat message, I "encoded" the project rules into the agent's instructions.

* **Insight:** System instructions are more powerful than individual prompts. The custom agent acted as a persistent project manager, ensuring that every diagram and code scaffold stayed "on-brand" for ByteBites.

### 3. Iterative Refinement over "One-Shot" Generation

I realized that the first output from an AI is rarely the final product. I used **Plan Mode** to align on logic before using **Edit Mode** to generate syntax. When I encountered an `AttributeError` during manual testing, it wasn't a failure of the AI, but a reminder that the human developer remains the final "judge of correctness."

* **Insight:** The workflow follows a loop: *Prompt → Review → Refine → Verify*. AI handles the "heavy lifting" of syntax, while I handle the "high-level" logic and debugging.

### 4. Verification through Descriptive Testing

In the final phase, I used AI to turn behavioral descriptions (e.g., "Check if the total is zero when the order is empty") into `pytest` code.

* **Insight:** This taught me to think about software requirements in plain English. If I can describe a behavior clearly, the AI can almost always implement the test for it.

## Conclusion

Working on ByteBites shifted my perspective from "How do I write this code?" to **"How do I guide the AI to build this system?"** Success in this new paradigm requires clear communication, rigorous verification, and the ability to maintain a mental model of the system even when the AI is doing the typing. I am no longer just a coder; I am an architect managing an AI workforce.
