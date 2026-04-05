# Auditor Agentic Pipeline Design

**Date:** 2026-04-04  
**Status:** Approved  
**Supersedes:** Initial single-agent AuditorAgent stub in `src/agents/auditor.py`

---

## 1. Problem

The original `AuditorAgent` was a single monolithic stub expected to detect all four pattern categories (lexical, structural, tonal, rhythmic) in one pass. This design has three problems:

1. **Scope mismatch** — Tier 1 detection is sentence-level, Tier 2 is paragraph-level, Tier 3 is article-level. A single agent cannot cleanly handle all three scopes.
2. **Wrong tool for the job** — Lexical tier detection is a vocabulary lookup (deterministic Python). Routing it through an LLM adds latency and non-determinism for no gain.
3. **Unmergeable output** — Structural, tonal, and rhythmic patterns are semantic judgments that need LLM reasoning. Mixing deterministic and semantic detection in one agent makes the result opaque and hard to test.

---

## 2. Architecture

Five components run sequentially, coordinated by a Python `HeadAuditor`. No LLM is involved in the orchestration layer.

```
article text
     │
     ▼
┌─────────────────────────┐
│  PythonLexicalDetector  │  ← pure Python, no Ollama
│  Tier 1/2/3 word match  │  → LexicalWordReport
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLMLexicalAgent        │  ← Ollama call
│  Synonym rotation,      │  → SubAgentReport (category=lexical)
│  significance inflation │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLMStructuralAgent     │  ← Ollama call
│  3-part lists,          │  → SubAgentReport (category=structural)
│  restated conclusions,  │
│  generic closers        │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLMTonalAgent          │  ← Ollama call
│  Hedging, sycophancy,   │  → SubAgentReport (category=tonal)
│  forced variation,      │
│  neutral voice          │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLMRhythmicAgent       │  ← Ollama call
│  Mechanical padding,    │  → SubAgentReport (category=rhythmic)
│  over-polished          │
│  uniformity             │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  HeadAuditor            │  ← pure Python, no Ollama
│  Pre-process, merge,    │  → AuditReport
│  verdict                │
└─────────────────────────┘
```

### Component locations

| Component | File | Ollama |
|---|---|---|
| `PythonLexicalDetector` | `src/detectors/lexical.py` | No |
| `LLMLexicalAgent` | `src/detectors/llm_lexical.py` | Yes |
| `LLMStructuralAgent` | `src/detectors/llm_structural.py` | Yes |
| `LLMTonalAgent` | `src/detectors/llm_tonal.py` | Yes |
| `LLMRhythmicAgent` | `src/detectors/llm_rhythmic.py` | Yes |
| `AuditorAgent` (HeadAuditor role) | `src/agents/auditor.py` | No |

The class stays named `AuditorAgent` — the public API `AuditorAgent.run(text, article_id) → AuditReport` is unchanged. "HeadAuditor" in this doc refers to the role, not a class rename. `review.py` and `app.py` require no modification.

---

## 3. Pattern-to-Category Mapping

| Pattern | Category | Detector |
|---|---|---|
| Tier 1 word hits (always flag) | lexical | PythonLexicalDetector |
| Tier 2 word cluster hits (≥2 per paragraph) | lexical | PythonLexicalDetector |
| Tier 3 density hits (≥3% of article) | lexical | PythonLexicalDetector |
| Synonym rotation | lexical | LLMLexicalAgent |
| Significance inflation | lexical | LLMLexicalAgent |
| Three-part list as default structure | structural | LLMStructuralAgent |
| Restated conclusions | structural | LLMStructuralAgent |
| Generic closers | structural | LLMStructuralAgent |
| Excessive hedging | tonal | LLMTonalAgent |
| Sycophantic openers | tonal | LLMTonalAgent |
| Forced variation / thesaurus abuse | tonal | LLMTonalAgent |
| Relentlessly neutral voice | tonal | LLMTonalAgent |
| Mechanical padding | rhythmic | LLMRhythmicAgent |
| Over-polished uniformity / no fragments | rhythmic | LLMRhythmicAgent |

### Deferred to Phase 2

The following patterns are skipped in this phase. They are either too strict to flag deterministically per-sentence or require richer context profiling:

- Sentence and paragraph length uniformity (per-sentence flagging)
- Bullet point and header density
- Vague attribution ("Experts believe", "Studies show")
- Copula avoidance ("serves as", "features", "boasts")

---

## 4. Schemas

### Layer 1 — Python Lexical Detector output

```python
class SentenceHit(BaseModel):
    sentence_id: str
    text: str
    matched_words: list[str]
    tier: int                        # 1, 2, or 3

class LexicalSummary(BaseModel):
    tier_1_hits: list[str]           # all tier-1 words found (article-level)
    tier_2_clusters: list[list[str]] # paragraph-level clusters
    tier_3_density: float            # ratio: tier-3 words / total words

class LexicalWordReport(BaseModel):
    lexical_summary: LexicalSummary
    sentence_hits: list[SentenceHit]
```

### Layer 2 — LLM sub-agent output (shared schema)

```python
class SubAgentFinding(BaseModel):
    sentence_id: str
    text: str
    patterns_found: list[str]                    # e.g. ["synonym rotation"]
    severity: Literal["low", "medium", "high"]
    suggested_fix: str

class SubAgentReport(BaseModel):
    category: Literal["lexical", "structural", "tonal", "rhythmic"]
    findings: list[SubAgentFinding]
```

All four LLM sub-agents return `SubAgentReport`. The `category` field is set by each agent to its own category.

### Layer 3 — Final output

```python
class FlaggedSentence(BaseModel):
    sentence_id: str
    text: str
    labels: dict[str, list[str]]       # {category: [pattern names]}
    suggested_fixes: dict[str, str]    # {category: suggested fix} — mirrors labels
    severity: Literal["low", "medium", "high"]
    is_flagged: bool

class AuditReport(BaseModel):
    article_id: str
    model: str
    verdict: Literal["patch", "structural_rewrite_needed"]
    flag_count: int
    category_count: int                            # how many of the 4 categories have ≥1 hit
    lexical_summary: LexicalSummary
    sub_reports: dict[str, SubAgentReport]         # raw per-category findings (for debugging)
    flagged_sentences: list[FlaggedSentence]       # merged sentence-centric view (for Rewriter)
```

**Note on `tier`:** `tier` is a lexical concept tied to the word list. It does not apply to structural, tonal, or rhythmic findings. `tier` lives on `SentenceHit` (Python detector output) and `LexicalSummary`, not on `FlaggedSentence`. `severity` is the unified signal in the final output.

**Note on `sub_reports`:** Kept in `AuditReport` for transparency during development. The Rewriter only reads `flagged_sentences`. `sub_reports` can be dropped in a later cleanup pass once agents are stable.

---

## 5. HeadAuditor Logic

### 5.1 Sentence pre-processing

Before any sub-agent runs, the article is split into sentences and assigned stable IDs:

```python
def _preprocess(self, text: str, article_id: str) -> dict[str, str]:
    """Returns {sentence_id: sentence_text}"""
    sentences = sent_tokenize(text)   # nltk sentence tokenizer
    return {
        f"{article_id}_s{str(i).zfill(2)}": s
        for i, s in enumerate(sentences)
    }
```

This dict is passed to every sub-agent so all `sentence_id` values are consistent across reports.

### 5.2 Merge algorithm

```
1. Run PythonLexicalDetector → LexicalWordReport
2. Run LLMLexicalAgent       → SubAgentReport (lexical)
3. Run LLMStructuralAgent    → SubAgentReport (structural)
4. Run LLMTonalAgent         → SubAgentReport (tonal)
5. Run LLMRhythmicAgent      → SubAgentReport (rhythmic)

6. Collect all sentence_ids with findings across all reports
7. For each unique sentence_id:
   a. Accumulate labels[category] from each source
   b. Accumulate suggested_fixes[category] from each source
   c. severity = max(severity across all findings for this sentence)
   d. is_flagged = True

8. Compute flag_count, category_count
9. Compute verdict
10. Return AuditReport
```

### 5.3 Verdict logic

```python
def _compute_verdict(
    lexical_summary: LexicalSummary,
    sub_reports: dict[str, SubAgentReport],
    flagged_sentences: list[FlaggedSentence],
    category_count: int,
) -> Literal["patch", "structural_rewrite_needed"]:
    rhythmic_flagged = len(sub_reports.get("rhythmic", SubAgentReport(
        category="rhythmic", findings=[]
    )).findings) > 0
    structural_flagged = len(sub_reports.get("structural", SubAgentReport(
        category="structural", findings=[]
    )).findings) > 0

    if (
        len(lexical_summary.tier_1_hits) >= settings.rewrite_vocab_threshold   # ≥5
        and category_count >= settings.rewrite_category_threshold               # ≥3
        and (rhythmic_flagged or structural_flagged)
    ):
        return "structural_rewrite_needed"
    return "patch"
```

All three thresholds are configurable via `config/settings.py`. Condition 3 uses LLM sub-agent output rather than a Python sentence-length calculation — the rhythmic agent assesses uniformity semantically, which avoids false positives on technical writing where uniform sentence length is appropriate.

---

## 6. File Changes

| File | Change |
|---|---|
| `src/agents/auditor.py` | `AuditorAgent` internals replaced with sub-agent orchestration. Schemas updated: `FlaggedSentence` (drop `tier`, `suggested_fix` → `suggested_fixes`), `AuditReport` (add `lexical_summary`, `sub_reports`). New schemas added: `SubAgentFinding`, `SubAgentReport`, `LexicalWordReport`, `LexicalSummary`, `SentenceHit`. |
| `src/detectors/` | New package. Five files: `lexical.py`, `llm_lexical.py`, `llm_structural.py`, `llm_tonal.py`, `llm_rhythmic.py`. |
| `src/agents/rewriter.py` | `FlaggedSentence` import still works — schema change is additive from Rewriter's perspective. May want to update to use `suggested_fixes` dict. |
| `review.py`, `src/ui/app.py` | No changes required. |

---

## 7. Out of Scope

- Parallel sub-agent execution (deferred — sequential is sufficient for now)
- Phase 2 patterns (sentence uniformity flagging, bullet/header density, vague attribution, copula avoidance)
- Rewriter pipeline redesign (separate brainstorming session)
