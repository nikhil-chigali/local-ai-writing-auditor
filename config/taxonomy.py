# Tell taxonomy sourced from github.com/conorbronsdon/avoid-ai-writing (MIT)
# Full 109-entry list to be populated from the reference skill.
# This file is data only — no detection logic lives here.

# Tier 1: Always flagged on any single occurrence
TIER_1: list[str] = [
    "delve", "leverage", "utilize", "commence", "facilitate",
    "synergy", "paradigm", "holistic", "seamlessly", "empower",
    "innovative", "cutting-edge", "game-changer", "transformative",
    "deep dive", "unpack", "boils down to", "at the end of the day",
]

# Tier 2: Flagged when >= 2 words cluster in the same paragraph
TIER_2: list[str] = [
    "nuanced", "comprehensive", "robust", "navigate", "landscape",
    "ecosystem", "framework", "dynamic", "multifaceted", "intricate",
    "streamline", "optimize", "foster", "enhance", "drive",
]

# Tier 3: Flagged only when density exceeds threshold across full article
TIER_3: list[str] = [
    "furthermore", "moreover", "notably", "it's worth noting",
    "in conclusion", "to summarize", "as mentioned", "as noted",
    "it is important to note that", "in order to",
]

# Four pattern categories — used for label keys in FlaggedSentence
PATTERNS: dict[str, list[str]] = {
    "lexical": [
        "overused AI vocabulary",
        "synonym rotation",
        "vague attribution",
        "significance inflation",
    ],
    "structural": [
        "excessive bullet points",
        "unnecessary headers",
        "three-part list default",
        "restated conclusion",
        "generic closer",
    ],
    "tonal": [
        "no personal anecdotes",
        "relentlessly neutral voice",
        "excessive hedging",
        "sycophantic opener",
        "forced variation",
    ],
    "rhythmic": [
        "uniform sentence length",
        "no fragments or asides",
        "mechanical padding",
    ],
}
