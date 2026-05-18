from __future__ import annotations

import re
from typing import Any

TECH_NEGATIVE = ["算法", "机器学习", "后端", "前端", "java", "c++", "测试开发", "运维", "software engineer", "backend", "frontend", "machine learning engineer", "research scientist"]
SALES_WORDS = ["销售", "sales", "商务"]
SALES_KEEP = ["ai", "genai", "saas", "云", "gtm", "sdr", "b2b", "出海", "海外", "api"]
JUNIOR_WORDS = ["实习", "intern", "校招", "2026", "应届", "new grad", "entry level", "助理", "管培"]
DOMESTIC_BONUS = ["北京", "上海", "杭州", "深圳", "广州", "成都", "南京", "苏州", "武汉", "西安", "remote", "远程"]


def normalize(text: str) -> str:
    return (text or "").lower().strip()


def contains_any(text: str, words: list[str]) -> list[str]:
    low = normalize(text)
    return [w for w in words if normalize(w) in low]


def summarize(text: str, max_len: int = 160) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def score_job(raw: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    title = raw.get("job_title") or raw.get("title") or ""
    company = raw.get("company") or ""
    location = raw.get("location") or ""
    desc = raw.get("description") or raw.get("jd_summary") or ""
    source = raw.get("source") or "unknown"
    url = raw.get("job_url") or raw.get("url") or ""
    text_all = f"{title} {company} {location} {desc}"

    strong = config.get("job_keywords", {}).get("strong", [])
    medium = config.get("job_keywords", {}).get("medium", [])
    exclude = config.get("exclude_keywords", [])
    target_locations = config.get("target_locations", [])

    matched_title = contains_any(title, strong)
    matched_desc = contains_any(text_all, strong)
    matched_medium = contains_any(text_all, medium)
    excluded = contains_any(text_all, exclude)
    junior = contains_any(text_all, JUNIOR_WORDS)
    loc_match = contains_any(location, target_locations) or contains_any(location, DOMESTIC_BONUS)

    score = 0
    reasons = []
    if matched_title:
        score += 35 + min(20, 5 * len(matched_title))
        reasons.append("标题命中强关键词：" + ", ".join(matched_title[:5]))
    if matched_desc:
        score += min(25, 4 * len(matched_desc))
        reasons.append("JD命中：" + ", ".join(matched_desc[:6]))
    if matched_medium:
        score += min(18, 2 * len(matched_medium))
    if junior:
        score += 15
        reasons.append("适合应届或实习：" + ", ".join(junior[:4]))
    if loc_match:
        score += 8
        reasons.append("地点匹配：" + (location or "未注明"))

    tech_hit = contains_any(title, TECH_NEGATIVE)
    if tech_hit and not contains_any(text_all, ["growth", "marketing", "community", "developer relations", "开发者生态", "产品运营"]):
        score -= 50
        reasons.append("扣分：疑似纯技术岗 " + ", ".join(tech_hit[:3]))

    sales_hit = contains_any(title, SALES_WORDS)
    if sales_hit and not contains_any(text_all, SALES_KEEP):
        score -= 20
        reasons.append("扣分：销售岗但缺少 AI/SaaS/出海/GTM 语境")

    if excluded:
        score -= min(35, 7 * len(excluded))
        reasons.append("排除词：" + ", ".join(excluded[:5]))

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("未明显命中核心方向，仅作为备选")

    return {
        "company": company,
        "job_title": title,
        "location": location,
        "job_url": url,
        "source": source,
        "jd_summary": summarize(desc),
        "matched_keywords": ", ".join(dict.fromkeys(matched_title + matched_desc + matched_medium)),
        "excluded_keywords": ", ".join(dict.fromkeys(excluded)),
        "score": score,
        "reason": "；".join(reasons),
        "posted_date": raw.get("posted_date", ""),
        "crawled_at": raw.get("crawled_at", ""),
    }


def rank_jobs(jobs: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    seen = set()
    scored = []
    for job in jobs:
        key = job.get("job_url") or f"{job.get('company')}::{job.get('job_title')}::{job.get('location')}"
        if key in seen:
            continue
        seen.add(key)
        scored.append(score_job(job, config))
    min_score = int(config.get("min_score", 35))
    return sorted([j for j in scored if j["score"] >= min_score], key=lambda x: x["score"], reverse=True)
