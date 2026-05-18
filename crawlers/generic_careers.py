from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 job-crawler/1.0"}
JOB_HINTS = ["intern", "growth", "marketing", "developer", "community", "product", "operation", "运营", "增长", "开发者", "海外", "出海", "市场", "实习", "校招", "AI", "API", "GTM", "SEM", "Affiliate"]
BAD_LINK_HINTS = ["privacy", "terms", "login", "signin", "cookie", "about", "contact", "news"]


def looks_like_job(text: str, href: str = "") -> bool:
    text = (text or "").strip()
    low = f"{text} {href}".lower()
    if not text or len(text) > 160:
        return False
    if any(b in low for b in BAD_LINK_HINTS):
        return False
    return any(h.lower() in low for h in JOB_HINTS)


def extract_location(text: str) -> str:
    locs = ["北京", "上海", "杭州", "深圳", "广州", "成都", "南京", "苏州", "武汉", "西安", "香港", "新加坡", "remote", "远程"]
    hit = [x for x in locs if x.lower() in (text or "").lower()]
    return ", ".join(hit)


def render_with_playwright(url: str, timeout: int = 20) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            html = page.content()
            browser.close()
            return html
    except Exception as exc:
        print(f"[playwright] render failed {url}: {exc}")
        return ""


def parse_html(name: str, url: str, html: str, source: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    crawled_at = datetime.now(timezone.utc).isoformat()
    seen = set()

    for a in soup.find_all("a"):
        title = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not href or not looks_like_job(title, href):
            continue
        job_url = urljoin(url, href)
        parent = a.find_parent()
        desc = parent.get_text(" ", strip=True) if parent else title
        key = job_url or f"{name}:{title}"
        if key in seen:
            continue
        seen.add(key)
        jobs.append({"company": name, "job_title": title, "location": extract_location(desc), "job_url": job_url, "source": source, "description": desc, "posted_date": "", "crawled_at": crawled_at})

    for node in soup.select("li, article, div"):
        text = node.get_text(" ", strip=True)
        if len(text) < 8 or len(text) > 260:
            continue
        if not looks_like_job(text):
            continue
        title = re.split(r"[|｜·•\n]", text)[0].strip()
        if len(title) > 120:
            title = title[:120]
        key = f"{name}:{title}:{extract_location(text)}"
        if key in seen:
            continue
        seen.add(key)
        jobs.append({"company": name, "job_title": title, "location": extract_location(text), "job_url": url, "source": source + "_textblock", "description": text, "posted_date": "", "crawled_at": crawled_at})
    return jobs


def crawl_company_page(name: str, url: str, timeout: int = 15) -> list[dict]:
    if not url:
        return []
    html = ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        print(f"[generic] requests failed {name}: {exc}")

    jobs = parse_html(name, url, html, "generic_careers") if html else []
    if not jobs:
        rendered = render_with_playwright(url, timeout=max(timeout, 20))
        if rendered:
            jobs = parse_html(name, url, rendered, "playwright_careers")
    return jobs
