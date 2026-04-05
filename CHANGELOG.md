# CHANGELOG

Architectural decisions, tradeoffs, and design changes — for portfolio review and interview discussion.

---

## [2026-04-04] — Bare-metal Ollama SDK over LangChain

**Decision:** Use the Ollama Python SDK directly rather than LangChain or LlamaIndex.
**Alternatives considered:** LangChain with Ollama integration, LlamaIndex.
**Rationale:** LangChain abstracts prompt construction, retry logic, and JSON parsing — exactly the parts that demonstrate engineering depth to interviewers. Bare-metal keeps everything explicit and visible. LangChain's Ollama integration also lags behind the native SDK.
**Tradeoffs:** More boilerplate. No built-in agent orchestration primitives (managed manually).

---

## [2026-04-04] — instructor for structured output enforcement

**Decision:** Use the `instructor` library wrapping Ollama to enforce Pydantic schema compliance on LLM outputs.
**Alternatives considered:** Manual JSON parsing with retries, LangChain output parsers.
**Rationale:** 3B models (llama3.2:3b) frequently violate JSON schemas. `instructor` retries with the validation error fed back to the model — significantly more reliable than manual parsing.
**Tradeoffs:** Adds a dependency. Retry loop adds latency on schema violations.

---

## [2026-04-04] — Langfuse over LangSmith for observability

**Decision:** Use Langfuse with `@observe()` decorator for tracing and model comparison.
**Alternatives considered:** LangSmith (requires LangChain), custom logging.
**Rationale:** Langfuse is framework-agnostic — works with bare-metal SDK via a decorator. Self-hostable. Provides prompt versioning, per-model latency, and token dashboards.
**Tradeoffs:** Less mature ecosystem than LangSmith. Requires a running Langfuse instance.

---

## [2026-04-04] — Scaffold as stubs, not working implementation

**Decision:** Build all modules as importable stubs (raise NotImplementedError) with full Pydantic schemas before any agent logic.
**Alternatives considered:** Implement top-down (auditor first, then rewriter).
**Rationale:** Forces schema design upfront. Enables import smoke tests immediately. Reveals schema inconsistencies before implementation begins.
**Tradeoffs:** None — this is standard practice for multi-module systems.

---

## [2026-04-04] — Auditor redesigned as phased sub-pipeline

**Decision:** Split the monolithic AuditorAgent into five components: PythonLexicalDetector + four LLM sub-agents (lexical, structural, tonal, rhythmic) + AuditorAgent as Python orchestrator.
**Alternatives considered:** Single monolithic AuditorAgent (original design), parallel sub-agent execution.
**Rationale:** Three problems with the original design: (1) tier 1/2/3 detection spans sentence/paragraph/article scope — hard to implement cleanly in one agent; (2) lexical tier detection is a vocabulary lookup — routing it through an LLM adds latency and non-determinism for no gain; (3) mixing deterministic and semantic detection in one agent makes the result opaque and untestable. Sequential execution chosen over parallel to keep the implementation simple — parallelization deferred.
**Tradeoffs:** More files, more components. 4 Ollama calls per article instead of 1. Sequential execution means higher total latency.

---

## [2026-04-04] — Lexical tier detection is pure Python (no LLM)

**Decision:** Tier 1/2/3 word detection uses Python string matching, not an LLM call.
**Alternatives considered:** LLM-based detection for all patterns.
**Rationale:** The word lists are fully enumerated. Tier 1 is a membership test. Tier 2 is a paragraph-level count. Tier 3 is a frequency ratio. These are deterministic operations. An LLM would add noise (missed words, hallucinated hits) and non-reproducibility.
**Tradeoffs:** Tier detection is exact-match only — no semantic understanding of context (e.g., "robust" in a technical blog may be fine). Context profiling deferred to Phase 2.

---

## [2026-04-04] — FlaggedSentence schema change: drop tier, singular→dict suggested_fix

**Decision:** Remove `tier: int` from FlaggedSentence. Change `suggested_fix: str` to `suggested_fixes: dict[str, str]` keyed by category.
**Alternatives considered:** Keep tier (set to 2 for non-lexical findings), keep single suggested_fix (take highest severity).
**Rationale:** `tier` is a lexical concept (word list tiers) and has no natural meaning for structural/tonal/rhythmic findings. `suggested_fix` as a single string loses category context when multiple sub-agents flag the same sentence. The dict mirrors the `labels` structure, making the schema self-consistent.
**Tradeoffs:** Schema change before labeling begins — acceptable because labeling has not started yet. Rewriter needs to be updated to consume `suggested_fixes` dict.

---

## [2026-04-04] — AuditReport carries both sub_reports and flagged_sentences

**Decision:** AuditReport includes both raw sub-agent outputs (sub_reports dict) and the merged sentence-centric view (flagged_sentences list).
**Alternatives considered:** Merged view only (sub_reports discarded after merge), raw sub_reports only (Rewriter reconstructs sentence view).
**Rationale:** During development, raw sub-reports are invaluable for debugging which sub-agent missed or over-flagged. The Rewriter only reads flagged_sentences. sub_reports can be dropped in a cleanup pass once agents are stable.
**Tradeoffs:** Redundant data in the output schema. Larger serialized output.

---

## [2026-04-04] — Verdict uses LLM rhythmic/structural signal, not Python stdev

**Decision:** The third condition in the patch/structural_rewrite_needed verdict uses LLM sub-agent findings (rhythmic or structural agent flagged anything) rather than a Python sentence-length standard deviation calculation.
**Alternatives considered:** Python stdev of sentence lengths with a threshold.
**Rationale:** The LLM rhythmic agent assesses uniformity semantically — it understands that a technical blog with uniform sentence structure is a different problem than a casual blog post. Python stdev cannot make this distinction.
**Tradeoffs:** Verdict is now dependent on LLM output, which is non-deterministic across runs. Accepted because the LLM output is the most signal-rich proxy available.

---

## [2026-04-04] — Deferred Phase 2 patterns

**Decision:** The following patterns are not implemented in Phase 1: sentence/paragraph length uniformity (per-sentence), bullet/header density, vague attribution, copula avoidance.
**Alternatives considered:** Implementing all patterns in Phase 1.
**Rationale:** These patterns are either too strict to flag deterministically per-sentence (over-flagging risk) or require context profiling (technical-blog vs. blog) not yet implemented.
**Tradeoffs:** Detection coverage is incomplete in Phase 1. Explicitly deferred, not forgotten.
