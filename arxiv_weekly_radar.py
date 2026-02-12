#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import arxiv
import pandas as pd
import requests

# =========================
# CONFIG
# =========================

BASE_DIR = Path("arxiv_radar_weekly")
BASE_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "arxiv_papers.csv"
SEEN_PATH = BASE_DIR / "seen_ids.txt"

DAYS_BACK = 7
TOTAL_PICKS = 10
RATIO = (6, 3, 1)

CATEGORIES = ["cs.CV", "cs.LG", "cs.RO", "cs.AI"]
MAX_RESULTS = 300
SLEEP_SEC = 0.2

MIN_HITS_ANY_BUCKET = 2

BUCKETS: Dict[str, List[str]] = {
    "P1_world_model_vla_3d": [
        "world model", "embodied", "vla", "vision-language-action",
        "visuomotor", "policy learning", "sim2real",
        "3d reconstruction", "multi-view", "structure from motion",
        "slam", "nerf", "gaussian splatting", "robot", "robotics"
    ],
    "P2_generative_ai": [
        "diffusion", "generative model", "foundation model",
        "video generation", "multimodal", "transformer"
    ],
    "P3_2d_cv": [
        "object detection", "segmentation",
        "multi-object tracking", "mot",
        "reid", "association", "id switch"
    ],
}

# =========================
# FUNCTIONS
# =========================

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def load_seen():
    if not SEEN_PATH.exists():
        return set()
    return set(SEEN_PATH.read_text(encoding="utf-8").splitlines())

def save_seen(seen):
    SEEN_PATH.write_text("\n".join(sorted(seen)), encoding="utf-8")

def count_hits(text, keywords):
    t = norm(text)
    hits = 0
    score = 0
    for kw in keywords:
        if kw in t:
            hits += 1
            score += 1
    return hits, score

def ratio_counts(total, ratio):
    a, b, c = ratio
    s = a + b + c
    x = int(round(total * a / s))
    y = int(round(total * b / s))
    z = total - x - y
    return x, y, z

# =========================
# MAIN
# =========================

def main():

    today_str = datetime.now().strftime("%Y-%m-%d")
    ARCHIVE_DIR = BASE_DIR / "archive" / today_str
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    MD_PATH = ARCHIVE_DIR / "weekly_top_picks.md"
    RIS_PATH = ARCHIVE_DIR / "weekly_picks.ris"

    since = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    seen = load_seen()

    cat_query = " OR ".join([f"cat:{c}" for c in CATEGORIES])
    search = arxiv.Search(
        query=f"({cat_query})",
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    rows = []

    for res in search.results():
        published = res.published.replace(tzinfo=timezone.utc)
        if published < since:
            continue

        pid = res.get_short_id().split("v")[0]
        if pid in seen:
            continue

        title = res.title.replace("\n", " ").strip()
        abstract = (res.summary or "").strip()
        blob = f"{title}\n{abstract}"

        best_bucket = None
        best_hits = 0
        best_score = -1

        for bname, kws in BUCKETS.items():
            hits, sc = count_hits(blob, kws)
            if sc > best_score:
                best_score = sc
                best_hits = hits
                best_bucket = bname

        if best_hits < MIN_HITS_ANY_BUCKET:
            continue

        rows.append({
            "pid": pid,
            "title": title,
            "authors": ", ".join(a.name for a in res.authors),
            "published": published.isoformat(),
            "url": res.entry_id,
            "bucket": best_bucket,
            "score": best_score,
            "abstract": abstract
        })

        seen.add(pid)
        time.sleep(SLEEP_SEC)

    save_seen(seen)

    if not rows:
        print("No new papers.")
        return

    df = pd.DataFrame(rows).sort_values(["score", "published"], ascending=[False, False])

    p1_quota, p2_quota, p3_quota = ratio_counts(TOTAL_PICKS, RATIO)

    p1 = df[df["bucket"].str.startswith("P1")].head(p1_quota)
    p2 = df[df["bucket"].str.startswith("P2")].head(p2_quota)
    p3 = df[df["bucket"].str.startswith("P3")].head(p3_quota)

    picks = pd.concat([p1, p2, p3]).head(TOTAL_PICKS)

    # Save Markdown
    md = [f"# Weekly Radar {today_str}\n"]
    for _, r in picks.iterrows():
        md.append(f"- **[{r['pid']}]({r['url']})**  \n"
                  f"  {r['title']}  \n"
                  f"  *{r['authors']}*  \n"
                  f"  _{r['abstract'][:300]}..._\n")

    MD_PATH.write_text("\n".join(md), encoding="utf-8")

    # Save RIS
    lines = []
    for _, r in picks.iterrows():
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {r['title']}")
        for au in r["authors"].split(","):
            lines.append(f"AU  - {au.strip()}")
        lines.append(f"UR  - {r['url']}")
        lines.append("ER  - ")
        lines.append("")

    RIS_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("Done.")
    print("Archive folder:", ARCHIVE_DIR)

if __name__ == "__main__":
    main()

