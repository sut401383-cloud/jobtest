from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

from crawlers.generic_careers import crawl_company_page
from feishu import build_message, send_feishu
from matcher import rank_jobs

OUTPUT_FIELDS = [
    "company", "job_title", "location", "job_url", "source", "jd_summary", "matched_keywords",
    "excluded_keywords", "score", "reason", "posted_date", "crawled_at"
]


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def crawl_all(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    timeout = int(config.get("request_timeout", 15))
    for item in config.get("company_urls", []):
        name = item.get("name", "")
        url = item.get("url", "")
        if not url:
            print(f"skip {name}: empty url")
            continue
        try:
            found = crawl_company_page(name, url, timeout=timeout)
            print(f"{name}: {len(found)} jobs")
            jobs.extend(found)
        except Exception as exc:
            print(f"{name}: crawler failed: {exc}")
    return jobs


def write_csv(jobs: list[dict[str, Any]], path: str = "jobs.csv") -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for job in jobs:
            writer.writerow({k: job.get(k, "") for k in OUTPUT_FIELDS})


def write_markdown(jobs: list[dict[str, Any]], total: int, path: str = "jobs.md") -> None:
    lines = ["# AI 出海岗位匹配日报", "", f"今日抓取岗位：{total} 个", f"有效匹配岗位：{len(jobs)} 个", "", "## Top 10"]
    if not jobs:
        lines.append("暂无达到分数线的岗位。请检查 config.yaml 里的 company_urls 或降低 min_score。")
    for i, job in enumerate(jobs[:10], 1):
        lines.extend([
            f"### {i}. {job['company']} - {job['job_title']}",
            f"- 地点：{job.get('location') or '未注明'}",
            f"- 分数：{job['score']}",
            f"- 匹配关键词：{job.get('matched_keywords') or '无'}",
            f"- 扣分词：{job.get('excluded_keywords') or '无'}",
            f"- 匹配原因：{job['reason']}",
            f"- 链接：{job['job_url']}",
            "",
        ])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = load_config()
    raw_jobs = crawl_all(config)
    ranked = rank_jobs(raw_jobs, config)
    max_results = int(config.get("max_results", 50))
    ranked = ranked[:max_results]
    write_csv(ranked)
    write_markdown(ranked, total=len(raw_jobs))
    print(f"Generated jobs.csv and jobs.md. raw={len(raw_jobs)}, matched={len(ranked)}")
    send_feishu(build_message(ranked, total=len(raw_jobs)))


if __name__ == "__main__":
    main()
