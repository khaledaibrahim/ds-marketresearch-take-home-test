from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

import pandas as pd
import yaml

from .io import project_root


TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def load_lexicons(path: Path | None = None) -> dict:
    source = path or project_root() / "config" / "lexicons.yml"
    with source.open() as handle:
        payload = yaml.safe_load(handle)

    base = {
        group: sorted({term.lower().strip() for term in terms if term})
        for group, terms in payload.items()
        if group != "category_overrides"
    }
    overrides_payload = payload.get("category_overrides", {})
    overrides = {
        category: {
            group: sorted({term.lower().strip() for term in terms if term})
            for group, terms in category_terms.items()
        }
        for category, category_terms in overrides_payload.items()
    }

    return {"base": base, "category_overrides": overrides}


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def category_lexicons(lexicons: dict, category_name: str | None = None) -> dict[str, list[str]]:
    combined = {group: list(terms) for group, terms in lexicons["base"].items()}
    if not category_name:
        return combined

    for group, terms in lexicons["category_overrides"].get(category_name, {}).items():
        combined.setdefault(group, [])
        combined[group] = sorted(set(combined[group]).union(terms))
    return combined


def score_text(
    text: str,
    lexicons: dict,
    category_name: str | None = None,
) -> dict[str, float]:
    active_lexicons = category_lexicons(lexicons, category_name)
    normalized = f" {text.lower()} "
    tokens = tokenize(text)
    token_count = max(len(tokens), 1)

    scores: dict[str, float] = {}
    for group, terms in active_lexicons.items():
        matches = 0
        for term in terms:
            term = term.lower().strip()
            if " " in term:
                matches += normalized.count(f" {term} ")
            else:
                matches += tokens.count(term)

        scores[f"{group}_matches"] = matches
        scores[f"{group}_share"] = matches / token_count

    scores["token_count"] = len(tokens)
    return scores


def score_text_frame(
    frame: pd.DataFrame,
    text_column: str,
    lexicons: dict | None = None,
    category_column: str | None = "category_name",
) -> pd.DataFrame:
    active_lexicons = lexicons or load_lexicons()
    if category_column and category_column in frame.columns:
        scored = frame.apply(
            lambda row: score_text(
                row.get(text_column, "") or "",
                active_lexicons,
                row.get(category_column),
            ),
            axis=1,
        )
    else:
        scored = frame[text_column].fillna("").map(
            lambda text: score_text(text, active_lexicons)
        )
    scored_df = pd.DataFrame(scored.tolist())
    return pd.concat([frame.reset_index(drop=True), scored_df], axis=1)


def score_texts(
    texts: Iterable[str],
    lexicons: dict | None = None,
    category_name: str | None = None,
) -> pd.DataFrame:
    active_lexicons = lexicons or load_lexicons()
    rows = [
        {"text": text, **score_text(text, active_lexicons, category_name)}
        for text in texts
    ]
    return pd.DataFrame(rows)
