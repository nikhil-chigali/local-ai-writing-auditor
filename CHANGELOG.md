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

## [2026-04-05] — Schema classes extracted to src/schemas/ package

**Decision:** Move all 9 Pydantic model classes (`SentenceHit`, `LexicalSummary`, `LexicalWordReport`, `SubAgentFinding`, `SubAgentReport`, `FlaggedSentence`, `AuditReport`, `RewriteResult`, `RewriteReport`) from `src/agents/auditor.py` and `src/agents/rewriter.py` into a dedicated `src/schemas/` package.
**Alternatives considered:** Leave schemas co-located with the agent that "owns" them; move all to a single flat `schemas.py`.
**Rationale:** Agents and detectors were mutually importing from `src.agents.auditor` — a detector importing from an agent module is a layering violation. The schemas are shared data contracts, not agent logic. A dedicated package makes imports unambiguous and enables Project #4 (LoRA fine-tuning) to import labels without pulling in agent dependencies.
**Tradeoffs:** One more package to navigate. The `src.agents.auditor` public surface shrinks — callers that imported schemas directly from it still work (re-exported at module level) but should migrate to `src.schemas`.

---

## [2026-04-07] — instructor.from_provider over from_openai for Ollama

**Decision:** Replace `instructor.from_openai(OpenAI(base_url="http://localhost:11434/v1"))` with `instructor.from_provider(f"ollama/{model}", mode=instructor.Mode.JSON)` across all 5 LLM callers.
**Alternatives considered:** `from_openai` with `mode=instructor.Mode.JSON` (Option A — documented but broken in practice for Ollama).
**Rationale:** `from_openai` without `Mode.JSON` defaults to tool-calling mode, which Ollama does not support. `from_provider` is the canonical Ollama integration path and was confirmed working. Also moves client instantiation from `_call_llm` (recreated per call) to `__init__` (created once), eliminating unnecessary object churn.
**Tradeoffs:** `from_provider` bakes the model name into the client — changing model at runtime requires a new client. Acceptable because model is set once at agent init.

---

## [2026-04-07] — Explicit JSON format hint in detector prompts

**Decision:** Add `Return JSON directly — do not wrap in any outer key: {"findings": [...]}` to the end of all 4 LLM detector prompts.
**Alternatives considered:** Overriding the Pydantic schema title via `model_config`; using `Mode.JSON_SCHEMA`.
**Rationale:** Mistral reads the JSON schema title (`_FindingsList`) that instructor embeds in the system message and uses it as a wrapper key around the response object. instructor then fails to validate `{"_FindingsList": {"findings": [...]}}` as `_FindingsList`. An explicit format instruction in the user prompt directly overrides this behaviour without requiring schema changes.
**Tradeoffs:** Prompt is slightly longer. If the class is renamed the hint still works (it references the field name, not the class name).

---

## [2026-04-07] — LANGFUSE_TRACING gate for env propagation

**Decision:** Add a `langfuse_tracing: bool = False` field to `Settings`. Langfuse keys are only propagated to `os.environ` (via `model_post_init`) when this flag is `True`.
**Alternatives considered:** Always propagate keys; propagate only when keys are non-empty.
**Rationale:** Langfuse SDK reads `os.environ` directly, not the settings object. Without propagation the SDK silently fails to authenticate. Gating behind a flag gives developers a single on/off switch without needing to remove keys from `.env`. Also prevents accidental tracing during pytest runs — `conftest.py` sets `LANGFUSE_TRACING=false` before any test runs.
**Tradeoffs:** One extra env var to document. Default `False` means tracing is opt-in, which is safer.

---

## [2026-04-07] — setuptools build-system for editable install

**Decision:** Add `[build-system]` and `[tool.setuptools.packages.find] where = ["."]` to `pyproject.toml`.
**Alternatives considered:** `sys.path` manipulation in entry points; `where = ["src"]` (would break `from src.agents...` imports).
**Rationale:** Streamlit adds the script directory (`src/ui/`) to `sys.path`, not the project root. Without an editable install, `src` only resolves when the CWD is the project root — it breaks at runtime when Streamlit launches. Adding a build-system causes `uv sync` to install the project itself, making `src` importable regardless of CWD.
**Tradeoffs:** `where = ["."]` exposes the top-level `src/` as a package rather than its sub-packages individually. Callers continue to use `from src.agents...` — no import path changes needed.

---

## [2026-04-07] — RewriterAgent implementation

**Decision:** RewriterAgent processes each `FlaggedSentence` individually (one LLM call per sentence), wraps the response in `_RewriteResultWrapper` to handle single-object schema enforcement, then string-substitutes rewrites into the original text.
**Alternatives considered:** Batch all flagged sentences in one LLM call; use a streaming rewrite.
**Rationale:** Per-sentence calls keep prompts small and focused, improving rewrite quality on smaller models. Batching risks one malformed sentence poisoning the entire response. The wrapper class is needed because instructor requires a Pydantic model at the top level — `RewriteResult` alone works but wrapping isolates the extraction cleanly.
**Tradeoffs:** N LLM calls for N flagged sentences — latency scales linearly. Accepted for Phase 1; batching deferred.

---

## [2026-04-07] — CLI uses Mode enum for --mode flag validation

**Decision:** Define a `Mode(str, enum.Enum)` with `rewrite` and `detect_only = "detect-only"` and type the `--mode` Typer argument with it.
**Alternatives considered:** Accept raw string, validate manually inside the command.
**Rationale:** Typer renders enum members as choices in `--help` and rejects invalid values before the command body runs. `detect-only` (hyphen) is the user-facing value; Python name uses underscore to remain a valid identifier.
**Tradeoffs:** None — this is the idiomatic Typer pattern.

---

## [2026-04-07] — Langfuse tracing disabled during pytest via conftest.py

**Decision:** Create `conftest.py` at project root that sets `os.environ["LANGFUSE_TRACING"] = "false"` before any test runs.
**Alternatives considered:** (A) disable tracing in conftest (chosen); (B) tag test traces with `session=test`; (C) spin up a local Langfuse instance for test traces.
**Rationale:** Test runs produce no meaningful traces — mocked LLM calls have no latency or token data. Polluting the Langfuse dashboard with test noise makes it harder to spot real production anomalies. Option A is the simplest and keeps the dashboard clean.
**Tradeoffs:** If integration tests against a real Ollama instance are added later, traces won't be captured. Acceptable — integration tests would need their own trace tagging strategy regardless.

---

## [2026-04-04] — Deferred Phase 2 patterns

**Decision:** The following patterns are not implemented in Phase 1: sentence/paragraph length uniformity (per-sentence), bullet/header density, vague attribution, copula avoidance.
**Alternatives considered:** Implementing all patterns in Phase 1.
**Rationale:** These patterns are either too strict to flag deterministically per-sentence (over-flagging risk) or require context profiling (technical-blog vs. blog) not yet implemented.
**Tradeoffs:** Detection coverage is incomplete in Phase 1. Explicitly deferred, not forgotten.
