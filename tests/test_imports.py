def test_import_settings():
    from config.settings import settings
    assert settings is not None


def test_import_taxonomy():
    from config.taxonomy import TIER_1, TIER_2, TIER_3, PATTERNS
    assert isinstance(TIER_1, list)
    assert isinstance(TIER_2, list)
    assert isinstance(TIER_3, list)
    assert isinstance(PATTERNS, dict)
