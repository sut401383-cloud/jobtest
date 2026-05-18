from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 job-crawler/1.0"}
JOB_HINTS = ["intern", "growth", "marketing", "developer", "community", "product", "运营", "增长", "开发者", "海外", "出海", "市场", "实习", "校招", "AI", "API", "GTM"]


def looks_like_job(text: str) -> bool:
    low = (text or "").lower()
    return any(h.lower() in low for h in JOB_HINTS) and len(text.strip()) <= 120


def crawl_company_page(name: str, url: str, timeout: int = 15) -> list[dict]:
    if not url:
        return []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[generic] skip {name}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    jobs: list[dict] = []
    crawled_at = datetime.now(timezone.utc).isoformat()

    for a in soup.find_all("a"):
        title = a.get_text(" ", strip=True)
        href = a.get("href")
        if not href or not looks_like_job(title):
            continue
        job_url = urljoin(url, href)
        parent = a.find_parent()
        desc = parent.get_text(" ", strip=True) if parent else title
        jobs.append({
            "company": name,
            "job_title": title,
            "location": "",
            "job_url": job_url,
            "source": "generic_careers",
            "description": desc,
            "posted_date": "",
            "crawled_at": crawled_at,
        })
    return jobs
