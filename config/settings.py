import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    default_model: str = "mistral"
    auditor_model: str = "mistral"
    rewriter_model: str = "mistral"

    # Tier 2: words must cluster in the same paragraph (>= threshold hits)
    tier2_cluster_threshold: int = 2
    # Tier 3: word frequency per total words must exceed threshold
    tier3_density_threshold: float = 0.03

    # Rewrite-vs-patch thresholds (all three must be met for structural rewrite)
    rewrite_vocab_threshold: int = 5
    rewrite_category_threshold: int = 3

    langfuse_tracing: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "http://localhost:3000"

    def model_post_init(self, __context) -> None:
        """Propagate Langfuse keys to os.environ so the SDK can autodiscover them."""
        if not self.langfuse_tracing:
            return
        if self.langfuse_public_key:
            os.environ.setdefault("LANGFUSE_PUBLIC_KEY", self.langfuse_public_key)
        if self.langfuse_secret_key:
            os.environ.setdefault("LANGFUSE_SECRET_KEY", self.langfuse_secret_key)
        if self.langfuse_base_url:
            os.environ.setdefault("LANGFUSE_BASE_URL", self.langfuse_base_url)


settings = Settings()
