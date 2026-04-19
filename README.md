# Local AI Writing Auditor

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20inference-black?logo=ollama)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic)
![instructor](https://img.shields.io/badge/instructor-structured%20output-6C3FC9)
![Langfuse](https://img.shields.io/badge/Langfuse-observability-FF6B35)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-49%20passing-brightgreen)
![Portfolio](https://img.shields.io/badge/Portfolio-Project%20%232%20of%205-blueviolet)

> Privacy-first, Ollama-powered two-agent pipeline that detects and rewrites AI writing tells.
> No cloud APIs. No data leaving your machine.

---

## Overview

AI-generated writing has a fingerprint — a set of structural, lexical, tonal, and rhythmic patterns that trained readers immediately recognise. This tool audits any article for those patterns and surgically rewrites the flagged sentences, preserving the author's voice and intent.

The architecture is a two-agent, two-pass pipeline running entirely on local models via Ollama. It is **Portfolio Project #2 of 5** in a GenAI Engineer portfolio series, designed to demonstrate local SLM deployment, agentic pipeline design, structured JSON output enforcement, and LLM evaluation infrastructure.

> Inspired by [github.com/conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) (MIT). The original contribution of this project is the local Ollama agent architecture — not the word list.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Two-Pass Pipeline                           │
│                                                                     │
│  Article Text                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────── Pass 1: AuditorAgent ────────────────────┐        │
│  │  PythonLexicalDetector  ──► Tier 1/2/3 word hits        │        │
│  │  LLMLexicalAgent        ──► synonym rotation, inflation  │        │
│  │  LLMStructuralAgent     ──► 3-part lists, generic closer │        │
│  │  LLMTonalAgent          ──► hedging, neutral voice       │        │
│  │  LLMRhythmicAgent       ──► padding, over-polish         │        │
│  └──────────────────────────┬──────────────────────────────┘        │
│                             │ AuditReport (JSON)                    │
│                             ▼                                       │
│                    ┌─────────────────┐                              │
│                    │  RewriterAgent  │  ← one LLM call per sentence │
│                    └───────┬─────────┘                              │
│                            │ RewriteReport (JSON)                   │
│                            ▼                                        │
│  ┌─────────────── Pass 2: AuditorAgent ────────────────────┐        │
│  │  Re-runs on rewritten text to catch surviving patterns   │        │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                     │
│  Output: Issues Found · Rewritten Version · What Changed · Pass 2  │
└─────────────────────────────────────────────────────────────────────┘
```

### Why Two Passes?

A single-pass rewrite misses patterns that only emerge after initial corrections — recycled transitions, subtle word swaps that sneak through. Pass 2 closes that gap and makes the pipeline visibly agentic.

### Rewrite vs. Patch Threshold

If all three conditions are met, the article is flagged for full structural rewrite rather than surgical patching:

- 5 or more flagged vocabulary hits across the article
- 3 or more distinct tell categories triggered
- `LLMRhythmicAgent` or `LLMStructuralAgent` flagged at least one finding

---

## Tell Taxonomy

Sourced from [github.com/conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) (MIT licensed). 109 entries across 3 tiers and 4 pattern categories.

### Three-Tier Word System

| Tier | Flagging Rule | Examples |
|------|--------------|---------|
| **Tier 1** | Always flagged on any occurrence | `delve`, `leverage`, `utilize`, `seamlessly`, `transformative` |
| **Tier 2** | Flagged when 2+ words cluster in the same paragraph | `nuanced`, `robust`, `ecosystem`, `landscape`, `streamline` |
| **Tier 3** | Flagged only at high density across the full article | `furthermore`, `moreover`, `it's worth noting`, `in conclusion` |

### Four Pattern Categories

| Category | Patterns Detected |
|----------|------------------|
| **Lexical** | Tier 1/2/3 word hits, synonym rotation, significance inflation |
| **Structural** | Three-part lists, restated conclusions, generic closers |
| **Tonal** | Excessive hedging, sycophantic openers, forced variation, neutral voice |
| **Rhythmic** | Mechanical padding, over-polished uniformity, no fragments or asides |

> **Design constraint:** Do not flag every word hit automatically. Over-flagging creates the very uniformity you're trying to remove. The tier system and clustering logic exist for this reason.

---

## Models

Three models run locally via Ollama. No cloud inference at any point.

| Model | Parameters | Ollama Tag | Role |
|-------|-----------|-----------|------|
| Llama 3.2 | 3B | `llama3.2:3b` | Speed baseline |
| Mistral | 7B | `mistral` | Balanced midpoint + LLM Judge |
| Phi-4 | 14B | `phi4` | Reasoning-focused, strong structured output |

Mistral is used as the LLM Judge for rewrite quality scoring — keeping the full evaluation pipeline local.

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.12 | Strong typing, ecosystem depth |
| Ollama interface | `instructor.from_provider` | Structured output with schema-enforced retries |
| Data validation | Pydantic v2 | Schema-locked sentence labels for Project #4 reuse |
| Observability | Langfuse `@observe()` | Framework-agnostic tracing, self-hostable |
| Dependency management | `uv` | Fast, modern toolchain |
| Config | pydantic-settings + `.env` | Model names and thresholds as config, not hardcode |
| Logging | loguru | Structured logs, zero boilerplate |
| UI | Streamlit | Two-panel flagged/rewrite display |
| CLI | Typer | `--mode detect-only` / `rewrite`, `--output-json` |
| Metrics | Custom Python + sklearn | Demonstrates eval infra knowledge |

**Why bare-metal SDK over LangChain:** LangChain abstracts prompt construction, retry logic, and JSON parsing — exactly the parts that demonstrate engineering depth. Bare-metal keeps everything explicit and visible. LangChain's Ollama integration also lags behind the native SDK.

**Why Langfuse over LangSmith:** Langfuse is framework-agnostic — one `@observe()` decorator, no framework coupling. Self-hostable. Same capabilities (prompt versioning, per-model latency, token dashboards) without requiring LangChain.

---

## Project Structure

```
local-ai-writing-auditor/
├── src/
│   ├── agents/
│   │   ├── auditor.py          # Agent 1 — orchestrates sub-pipeline
│   │   └── rewriter.py         # Agent 2 — per-sentence rewriter
│   ├── detectors/
│   │   ├── lexical.py          # PythonLexicalDetector (no LLM)
│   │   ├── llm_lexical.py      # LLMLexicalAgent
│   │   ├── llm_structural.py   # LLMStructuralAgent
│   │   ├── llm_tonal.py        # LLMTonalAgent
│   │   └── llm_rhythmic.py     # LLMRhythmicAgent
│   ├── schemas/
│   │   ├── audit.py            # AuditReport, FlaggedSentence, SubAgentFinding
│   │   ├── lexical.py          # LexicalSummary, LexicalWordReport, SentenceHit
│   │   └── rewrite.py          # RewriteReport, RewriteResult
│   ├── eval/
│   │   ├── metrics.py          # Precision / recall / F1 (planned)
│   │   └── judge.py            # LLM-as-judge rewrite scorer (planned)
│   └── ui/
│       └── app.py              # Streamlit application
├── config/
│   ├── settings.py             # pydantic-settings config
│   └── taxonomy.py             # 3-tier word list + pattern categories
├── data/
│   ├── gold_dataset/           # 30 labeled articles (JSON) — planned
│   └── articles/               # Raw article sources
├── tests/
│   ├── conftest.py             # Disables Langfuse tracing during tests
│   ├── test_auditor.py
│   ├── test_rewriter.py
│   ├── test_lexical_detector.py
│   └── test_imports.py
├── review.py                   # CLI entrypoint
├── pyproject.toml
└── .env                        # Langfuse keys, model config
```

---

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `pip install uv`
- [Ollama](https://ollama.com) running locally

### Install

```bash
git clone https://github.com/nikhil-chigali/local-ai-writing-auditor.git
cd local-ai-writing-auditor
uv sync
```

### Pull Models

```bash
ollama pull mistral
ollama pull llama3.2:3b
ollama pull phi4
```

### Configure

```bash
cp .env.example .env
# Edit .env — add Langfuse keys if you want tracing, or leave LANGFUSE_TRACING=false
```

`.env` reference:

```env
LANGFUSE_TRACING=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
DEFAULT_MODEL=mistral
```

---

## Usage

### CLI

```bash
# Full pipeline: detect + rewrite + second-pass audit
uv run python review.py --file article.md --model mistral

# Detect only — no rewrite
uv run python review.py --file article.md --model llama3.2:3b --mode detect-only

# Dump full JSON report to file
uv run python review.py --file article.md --model mistral --output-json report.json
```

### Streamlit UI

```bash
uv run streamlit run src/ui/app.py
```

Paste article text in the left panel. Select model and mode from the sidebar. Click **Run Audit** to see flagged sentences, rewrites, what changed, and the second-pass audit result.

### Tests

```bash
uv run pytest
uv run pytest --cov=src --cov-report=term-missing
```

---

## Output Format

Each run returns four sections:

| Section | Contents |
|---------|----------|
| **Issues Found** | Every AI tell identified, with flagged text quoted and severity |
| **Rewritten Version** | Clean version with AI tells surgically removed |
| **What Changed** | Plain-language summary of each rewrite and why |
| **Second-Pass Audit** | Any patterns that survived the first rewrite |

---

## Progress

### Completed

- [x] **Scaffold** — all Pydantic schemas defined and locked (`FlaggedSentence`, `AuditReport`, `RewriteReport`, `RewriteResult`)
- [x] **Schema package** — extracted to `src/schemas/` (eliminates circular imports, enables Project #4 reuse without pulling in agent dependencies)
- [x] **PythonLexicalDetector** — Tier 1/2/3 word detection via pure Python (no LLM)
- [x] **Four LLM sub-agents** — lexical, structural, tonal, rhythmic pattern detection via Ollama + `instructor`
- [x] **AuditorAgent** — Python orchestrator; merges sub-agent outputs into `AuditReport`, computes rewrite/patch verdict
- [x] **RewriterAgent** — per-sentence rewriter via `instructor`, two-pass pipeline wired end-to-end
- [x] **CLI** — Typer with `--mode detect-only/rewrite`, `--output-json`, Rich-formatted four-section output
- [x] **Streamlit UI** — two-column layout, severity-coloured sentence cards, What Changed and Second-Pass expanders
- [x] **Langfuse observability** — `@observe()` on all agent `run()` methods, gated behind `LANGFUSE_TRACING` flag
- [x] **Test suite** — 49 tests passing; Langfuse disabled in pytest via `conftest.py`

### Planned

- [ ] **Gold evaluation dataset** — 30 labeled articles (10 human / 10 AI / 10 human-edited-AI)
- [ ] **Evaluation harness** — precision, recall, F1 per category; LLM-as-judge rewrite quality scorer
- [ ] **Three-model benchmark** — Llama 3.2 3B vs Mistral 7B vs Phi-4 14B; benchmark CSV + rich table output
- [ ] **Synthetic sentence generator** — expands the gold dataset for Project #4 LoRA fine-tuning
- [ ] **README enhancements** — architecture diagram, model comparison table, Langfuse trace screenshot, demo GIF
- [ ] **Project #4 bridge** — export gold dataset and baseline metrics for LoRA fine-tuning

---

## Key Technical Decisions & Tradeoffs

### `instructor.from_provider` over `from_openai`

`instructor.from_openai(OpenAI(...))` without `mode=instructor.Mode.JSON` defaults to tool-calling mode, which Ollama does not support. `instructor.from_provider(f"ollama/{model}", mode=instructor.Mode.JSON)` is the canonical Ollama integration path. The tradeoff: the model name is baked into the client at init time — changing model at runtime requires a new client. Acceptable because model is set once per agent.

### Explicit JSON format hint in detector prompts

Mistral reads the JSON schema title (the Python class name) that instructor embeds in the system message and wraps its response in that key — producing `{"_FindingsList": {"findings": [...]}}` instead of `{"findings": [...]}`. Each detector prompt includes an explicit format instruction at the end to override this. This is a prompt-level fix rather than a schema-level one: more robust because it survives class renames.

### Schemas extracted to `src/schemas/`

Detectors and agents were circularly importing from `src.agents.auditor`. Schemas are shared data contracts, not agent logic. The dedicated package eliminates the layering violation and allows Project #4 to import sentence labels without pulling in agent dependencies.

### Lexical detection is pure Python, not LLM

Tier 1/2/3 detection uses exact string matching. The word lists are fully enumerated. Tier 1 is a membership test. Tier 2 is a paragraph-level cluster count. Tier 3 is a frequency ratio. Routing deterministic operations through an LLM would add noise, non-reproducibility, and unnecessary latency.

### `LANGFUSE_TRACING` gate

Langfuse SDK reads `os.environ` directly — pydantic-settings alone doesn't propagate values there. `model_post_init` in `Settings` propagates Langfuse keys to `os.environ` only when `LANGFUSE_TRACING=true`. Default is `false`. `conftest.py` enforces `false` during pytest runs to keep the observability dashboard clean of meaningless test traces.

### Editable install via setuptools

Streamlit adds its script directory (`src/ui/`) to `sys.path`, not the project root. Without an editable install, `from src.agents...` fails at Streamlit runtime regardless of how you launch it. Adding `[build-system]` + `[tool.setuptools.packages.find] where = ["."]` to `pyproject.toml` causes `uv sync` to install the project itself, making `src` importable from any working directory.

### Per-sentence rewriting

The Rewriter processes each `FlaggedSentence` individually — one LLM call per sentence. Batching risks one malformed sentence poisoning the entire response object. Per-sentence calls keep prompts small and focused, which improves rewrite quality particularly on smaller (3B) models. Latency scales linearly with flag count; batching is an explicit future optimisation.

---

## Project #4 Bridge — LoRA Fine-Tuning

This project is designed so its outputs feed directly into Portfolio Project #4.

**The narrative:**
> *Project #2: Agentic detection via prompt engineering. ~71% F1, ~340ms/article.*
> *Project #4: Same eval set, LoRA-fine-tuned sentence classifier. ~89% F1, ~40ms/article.*
> Same data. Measurable improvement. Documented tradeoffs.

**Commitments made here to enable Project #4:**

| Commitment | Why |
|------------|-----|
| `FlaggedSentence` schema locked — no field name or type changes after labeling | Schema change = full re-label of 30 articles |
| Precision/recall/F1 measured per category | These become Project #4's improvement baseline |
| Synthetic sentence generator committed (unused here) | Provides training data expansion path for fine-tuning |

**Two paradigms, not a replacement:** Prompt-based detection is flexible, zero training cost, interpretable, and slower. A fine-tuned classifier is faster, more consistent, higher F1 — but narrow and requires labeled data. Project #4 benchmarks both on the same eval set.

---

## Credits

Tell taxonomy (109-entry word replacement table, 3-tier system, 4 pattern categories):
**[github.com/conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) — MIT licensed**

The original contribution of this project is the local Ollama agent architecture, two-pass agentic pipeline, structured JSON output layer, gold evaluation dataset, multi-model benchmarking harness, and Streamlit/CLI interface.

---

## Portfolio Context

| # | Project | Core Skill Demonstrated |
|---|---------|------------------------|
| 1 | Production RAG | Retrieval-augmented generation, vector DBs |
| **2** | **Local AI Writing Auditor (this)** | **Local SLM deployment, agentic pipelines, evals** |
| 3 | LLM Observability | Tracing, logging, monitoring LLM systems |
| 4 | LoRA Fine-Tuning | Fine-tune classifier on Project #2 gold dataset |
| 5 | Real-Time Multimodal Voice | Streaming, multimodal, latency-sensitive systems |
