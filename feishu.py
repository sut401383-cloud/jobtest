from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

import requests


def sign(secret: str, timestamp: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(string_to_sign, b"", digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def build_message(jobs: list[dict[str, Any]], total: int) -> str:
    lines = [f"今日抓取岗位数量：{total}", "", "Top 10 最匹配岗位："]
    if not jobs:
        lines.append("暂无达到分数线的岗位。请检查 company_urls 或降低 min_score。")
    for i, job in enumerate(jobs[:10], 1):
        lines.extend([
            f"{i}. {job['company']} - {job['job_title']}",
            f"地点：{job.get('location') or '未注明'}｜分数：{job['score']}",
            f"原因：{job['reason']}",
            f"链接：{job['job_url']}",
            "",
        ])
    lines.append("jobs.csv 和 jobs.md 已生成。")
    return "\n".join(lines)


def send_feishu(text: str) -> None:
    webhook = os.getenv("FEISHU_WEBHOOK_URL")
    secret = os.getenv("FEISHU_SECRET")
    if not webhook:
        print("FEISHU_WEBHOOK_URL not set; skip Feishu push.")
        return

    payload: dict[str, Any] = {"msg_type": "text", "content": {"text": text}}
    if secret:
        timestamp = str(int(time.time()))
        payload["timestamp"] = timestamp
        payload["sign"] = sign(secret, timestamp)

    resp = requests.post(webhook, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
    if resp.status_code >= 400:
        raise RuntimeError(f"Feishu push failed: {resp.status_code} {resp.text}")
    print("Feishu push sent.")
