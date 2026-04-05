from pydantic import BaseModel


class RewriteResult(BaseModel):
    sentence_id: str
    original: str
    rewritten: str
    change_summary: str


class RewriteReport(BaseModel):
    article_id: str
    model: str
    rewrites: list[RewriteResult]
    full_rewritten_text: str
