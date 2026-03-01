#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import re
import time
from io import BytesIO
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import arxiv
import pandas as pd
import requests
from pypdf import PdfReader

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

OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TIMEOUT_SEC = 45
OPENAI_API_KEY_FILE = Path.home() / ".arxiv_radar" / "openai_api_key.txt"
PDF_TEXT_MAX_CHARS = 12000
PDF_READ_MAX_PAGES = 6

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



def resolve_openai_key_file() -> Path:
    env_key_file = os.getenv("OPENAI_API_KEY_FILE", "").strip()
    if env_key_file:
        return Path(env_key_file).expanduser()

    appdata = os.getenv("APPDATA", "").strip()
    if appdata:
        return Path(appdata) / "arxiv-radar" / "openai_api_key.txt"

    return OPENAI_API_KEY_FILE


def load_openai_api_key() -> str:
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key

    key_file = resolve_openai_key_file()
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    return ""

def extract_pdf_text(pdf_url: str) -> str:
    if not pdf_url:
        return ""

    try:
        resp = requests.get(pdf_url, timeout=OPENAI_TIMEOUT_SEC)
        resp.raise_for_status()
        reader = PdfReader(BytesIO(resp.content))

        chunks = []
        for page in reader.pages[:PDF_READ_MAX_PAGES]:
            page_text = (page.extract_text() or "").strip()
            if page_text:
                chunks.append(page_text)

        text = "\n".join(chunks).strip()
        return text[:PDF_TEXT_MAX_CHARS]
    except Exception:
        return ""


def format_cn_overview(overview: str) -> str:
    lines = [line.strip(" -•\t") for line in overview.splitlines() if line.strip()]
    if not lines:
        return "  - （中文文章概述生成失败）"
    return "\n".join(f"  - {line}" for line in lines[:3])

def build_chinese_digest(title: str, abstract: str, pdf_text: str) -> Tuple[str, str]:
    api_key = load_openai_api_key()
    if not api_key:
        return "（未配置 OpenAI API Key，未生成中文摘要）", "（未配置 OpenAI API Key，未生成中文文章概述）"

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    prompt = (
        "请你优先根据论文 PDF 正文内容生成结果；若 PDF 内容不足，再参考摘要。"
        "输出一个 JSON 对象，包含两个字段："
        "cn_summary（中文摘要，80~120字）和 cn_overview（中文文章概述，3个要点，每点一行，突出方法、结果和意义）。"
        "仅输出 JSON，不要输出额外文字。"
    )
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "你是一个严谨的科研助手。"},
            {"role": "user", "content": f"标题：{title}\n\nPDF正文节选：{pdf_text or '（未成功读取PDF正文）'}\n\n摘要：{abstract}\n\n{prompt}"},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=OPENAI_TIMEOUT_SEC)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        cn_summary = str(parsed.get("cn_summary", "")).strip()
        cn_overview = str(parsed.get("cn_overview", "")).strip()
        if not cn_summary:
            cn_summary = "（中文摘要生成失败）"
        if not cn_overview:
            cn_overview = "（中文文章概述生成失败）"
        return cn_summary, cn_overview
    except Exception as e:
        return (
            f"（中文摘要生成失败：{e}）",
            f"（中文文章概述生成失败：{e}）",
        )

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
            "abstract": abstract,
            "pdf_url": getattr(res, "pdf_url", "")
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
        pdf_text = extract_pdf_text(str(r.get("pdf_url", "")))
        cn_summary, cn_overview = build_chinese_digest(r["title"], r["abstract"], pdf_text)
        md.append(f"- **[{r['pid']}]({r['url']})**  \n"
                  f"  {r['title']}  \n"
                  f"  *{r['authors']}*  \n"
                  f"  _{r['abstract'][:300]}..._\n"
                  f"  **中文摘要：**{cn_summary}  \n"
                  f"  **中文文章概述：**\n{format_cn_overview(cn_overview)}\n")

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
