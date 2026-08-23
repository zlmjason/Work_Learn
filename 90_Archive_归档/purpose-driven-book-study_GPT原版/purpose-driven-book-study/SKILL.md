---
name: purpose-driven-book-study
description: Build and run a purpose-driven, dialectical study program for technical books, textbooks, papers, standards, manuals, and long PDFs. Use when the user wants to systematically learn, deeply read, study, or精读 a book or document; wants a learning route tied to a current project or workstream; or asks for staged summaries instead of reading mechanically from beginning to end.
---

# Purpose-Driven Book Study

Study toward a capability or work problem, not toward page completion. Treat the table of contents as a knowledge index rather than a mandatory sequence.

## Core rules

1. Establish the book's whole-system view before teaching individual sections.
2. Identify the user's current workstream, intended capability, and concrete problems. Use visible context first; ask only for missing information that would materially change the route.
3. Organize learning around questions, mechanisms, and dependencies. Do not default to chapter order.
4. Classify source material as `deep read`, `supporting read`, `skim`, or `defer` and explain the choice.
5. Read dialectically: distinguish claims, mechanisms, evidence, assumptions, boundaries, counterexamples, and transfer conditions.
6. Keep the source's claims separate from interpretation, external verification, and workstream-specific extension.
7. End every conceptual stage with a persistent Markdown summary tied to the current workstream.
8. Revise the route when new questions or misconceptions reveal a better dependency order.

## Workflow

### 1. Audit the source

Inspect enough of the source to establish:

- author purpose and central problem;
- intended audience and prerequisites;
- overall argument or knowledge structure;
- chapter roles and dependency relationships;
- evidence type: experiments, derivations, cases, specifications, or experience;
- scope exclusions, platform assumptions, edition limits, and translation issues;
- what the source can and cannot answer for the user's work.

For long PDFs, inspect the metadata, table of contents, preface/introduction, chapter openings, chapter summaries, appendices, and selected representative pages before proposing the route. Use the appropriate file-format skill when available.

### 2. Produce the orientation map

Before detailed study, present:

- what the whole source is trying to teach;
- its central mental model;
- the major capability modules hidden behind the chapter structure;
- its relevance and limitations for the active workstream;
- the proposed question-driven route and why this order is useful;
- stage boundaries and expected outputs.

Create or update `00-学习路线与问题地图.md` when the study becomes an ongoing project. Use the template in `references/document-templates.md`.

### 3. Build the question-driven route

For each module, specify:

| Field | Required content |
|---|---|
| Core question | The problem the learner should be able to answer |
| Capability outcome | What the learner should be able to explain, diagnose, design, or verify |
| Source map | Relevant chapters/sections/pages, possibly non-contiguous |
| Reading depth | Deep read, supporting read, skim, or defer |
| Workstream link | Current task, design decision, failure mode, or test item it informs |
| Verification | Exercise, calculation, code, experiment, diagram, or teach-back |
| Stage output | The summary document or reusable artifact to create |

Reorder modules by conceptual dependency and work value. Allow targeted detours into supporting sources when the primary source assumes missing knowledge or makes platform-specific claims.

### 4. Teach each learning unit

Use this sequence unless the material requires another order:

1. **Question:** What are we trying to understand or decide?
2. **Source position:** What does the source claim, and where?
3. **Mechanism:** Why does it work this way at the relevant abstraction levels?
4. **Evidence:** What data, derivation, example, or specification supports it?
5. **Boundary:** Under what architecture, workload, version, or assumption is it valid?
6. **Challenge:** What counterexample, alternative explanation, or tradeoff could change the conclusion?
7. **Transfer:** How does it map to the user's current system and workstream?
8. **Verification:** How would the learner test, measure, or falsify the conclusion?

Explain prerequisite concepts on demand. Prefer causal chains over term lists. Use diagrams or tables only when they materially clarify structure, timing, or mappings.

### 5. Maintain source discipline

Label distinctions clearly:

- **Source claim:** stated or directly supported by the source;
- **Interpretation:** a synthesis or explanation derived from the source;
- **Extension:** application to the user's workstream;
- **Verification:** confirmation or disagreement from a specification, experiment, or current authoritative source.

Do not silently translate conclusions across architectures. For example, identify what changes when moving from an out-of-order server CPU to an in-order MCU, or from explanatory textbook material to normative vendor documentation.

For standards and reference manuals, preserve normative language, version, register conditions, reset behavior, and implementation-defined boundaries. Do not let a secondary source override a primary specification without explicit evidence.

### 6. Close each stage

A stage ends when a coherent capability has been built, not after an arbitrary page count. At stage closure:

1. Reconstruct the mechanism without merely paraphrasing sections.
2. Record conclusions, evidence, boundaries, unresolved conflicts, and corrected misconceptions.
3. Explain the relationship to the current workstream at three levels:
   - direct application now;
   - reusable engineering method;
   - longer-term architecture or career insight.
4. Convert insights into concrete actions: tests, measurements, code checks, design reviews, or follow-up questions.
5. Create a persistent Markdown stage summary using `references/document-templates.md`.
6. Update the living route if priorities or dependencies changed.

Do not create a shallow summary after every small section. Summarize at meaningful conceptual milestones or when the user explicitly requests a checkpoint.

### 7. Finish with synthesis

At the end of the source or learning objective, produce:

- a knowledge map organized by mechanisms and engineering questions;
- a claim-to-evidence-to-boundary matrix;
- the most important workstream decisions influenced by the study;
- a backlog of experiments and unresolved questions;
- a list of knowledge that was deliberately deferred;
- a concise guide explaining when to reopen which source sections.

## Interaction style

- Start each session by stating the current stage, core question, and why it matters now.
- Lead with a mental model, then deepen into mechanisms and evidence.
- Invite challenges and alternative explanations; do not treat the book as automatically correct.
- Correct translation, edition, and platform mismatches explicitly.
- Avoid dumping an entire chapter when one causal question is the useful learning unit.
- When the user asks an interruption question, answer it fully and then place it back into the route.
- Preserve useful user examples, project constraints, and validated conclusions in the next stage document.

## Templates

Read `references/document-templates.md` before creating the initial route document, a stage summary, or the final synthesis.
