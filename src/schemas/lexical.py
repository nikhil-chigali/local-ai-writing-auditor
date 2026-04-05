from pydantic import BaseModel


class SentenceHit(BaseModel):
    sentence_id: str
    text: str
    matched_words: list[str]
    tier: int  # 1, 2, or 3


class LexicalSummary(BaseModel):
    tier_1_hits: list[str]            # all tier-1 words found (article-level)
    tier_2_clusters: list[list[str]]  # paragraph-level clusters
    tier_3_density: float             # ratio: tier-3 words / total words


class LexicalWordReport(BaseModel):
    lexical_summary: LexicalSummary
    sentence_hits: list[SentenceHit]
