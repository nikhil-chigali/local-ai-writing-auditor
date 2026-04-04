import pandas as pd

CATEGORIES = ["lexical", "structural", "tonal", "rhythmic"]


def compute_metrics(
    gold_labels: list[dict],
    predicted_labels: list[dict],
) -> pd.DataFrame:
    """Compute precision, recall, and F1 per tell category plus overall.

    Args:
        gold_labels: List of sentence dicts from gold dataset.
                     Each dict must have keys: sentence_id, labels (dict of category -> list[str]),
                     is_flagged (bool).
        predicted_labels: List of sentence dicts in the same shape from model output.

    Returns:
        DataFrame with columns: category, precision, recall, f1.
        Rows: one per category in CATEGORIES, plus an "overall" row.
    """
    raise NotImplementedError
