from config.settings import settings
from config.taxonomy import TIER_1, TIER_2, TIER_3
from src.agents.auditor import LexicalSummary, LexicalWordReport, SentenceHit


class PythonLexicalDetector:
    """Detects Tier 1/2/3 vocabulary hits deterministically. No Ollama."""

    def run(
        self,
        sentences: dict[str, str],
        paragraphs: list[list[str]],
    ) -> LexicalWordReport:
        tier1_hits = self._scan_tier1(sentences)
        tier2_hits, tier2_clusters = self._scan_tier2(sentences, paragraphs)
        tier3_density = self._compute_tier3_density(sentences)

        # Merge tier1 and tier2 hits per sentence_id
        merged: dict[str, SentenceHit] = {}
        for hit in tier1_hits + tier2_hits:
            if hit.sentence_id not in merged:
                merged[hit.sentence_id] = hit
            else:
                existing = merged[hit.sentence_id]
                merged[hit.sentence_id] = SentenceHit(
                    sentence_id=hit.sentence_id,
                    text=hit.text,
                    matched_words=list(set(existing.matched_words + hit.matched_words)),
                    tier=min(existing.tier, hit.tier),
                )

        tier1_words_found = list({w for h in tier1_hits for w in h.matched_words})

        return LexicalWordReport(
            lexical_summary=LexicalSummary(
                tier_1_hits=tier1_words_found,
                tier_2_clusters=tier2_clusters,
                tier_3_density=tier3_density,
            ),
            sentence_hits=list(merged.values()),
        )

    def _scan_tier1(self, sentences: dict[str, str]) -> list[SentenceHit]:
        hits = []
        for sid, text in sentences.items():
            text_lower = text.lower()
            matched = [w for w in TIER_1 if w.lower() in text_lower]
            if matched:
                hits.append(SentenceHit(
                    sentence_id=sid, text=text, matched_words=matched, tier=1
                ))
        return hits

    def _scan_tier2(
        self,
        sentences: dict[str, str],
        paragraphs: list[list[str]],
    ) -> tuple[list[SentenceHit], list[list[str]]]:
        sentence_hits: list[SentenceHit] = []
        clusters: list[list[str]] = []

        for para_ids in paragraphs:
            para_matches: list[tuple[str, str]] = []  # (sentence_id, word)
            for sid in para_ids:
                text_lower = sentences.get(sid, "").lower()
                for word in TIER_2:
                    if word.lower() in text_lower:
                        para_matches.append((sid, word))

            if len(para_matches) >= settings.tier2_cluster_threshold:
                clusters.append([w for _, w in para_matches])

                by_sentence: dict[str, list[str]] = {}
                for sid, word in para_matches:
                    by_sentence.setdefault(sid, []).append(word)

                for sid, words in by_sentence.items():
                    sentence_hits.append(SentenceHit(
                        sentence_id=sid,
                        text=sentences[sid],
                        matched_words=words,
                        tier=2,
                    ))

        return sentence_hits, clusters

    def _compute_tier3_density(self, sentences: dict[str, str]) -> float:
        all_text = " ".join(sentences.values())
        total_words = len(all_text.split())
        if total_words == 0:
            return 0.0
        all_text_lower = all_text.lower()
        count = sum(all_text_lower.count(phrase.lower()) for phrase in TIER_3)
        return count / total_words
